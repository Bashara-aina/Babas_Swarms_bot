"""chandra_client.py — Chandra OCR 2 integration for swarm-bot.

Provides async wrappers around the chandra-ocr package for:
  - Images (JPEG, PNG, WebP, etc.)
  - Multi-page PDFs
  - Screenshot / screen-capture bytes

Supports both vLLM (default, recommended) and HuggingFace backends.
Falls back to pytesseract if Chandra is unavailable.

Usage:
    result = await chandra_ocr_image("/path/to/image.png")
    result = await chandra_ocr_pdf("/path/to/file.pdf", pages="1-5")
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ChandraResult:
    markdown: str
    html: str
    raw: str
    token_count: int
    page_count: int
    source: str  # "chandra_vllm" | "chandra_hf" | "pytesseract"
    error: bool
    error_message: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Lazy Chandra import (avoids import-time failure when Chandra isn't installed)
# ─────────────────────────────────────────────────────────────────────────────

_chandra_available: bool | None = None
_chandra_model = None
_hf_processor = None


def _check_chandra_available() -> bool:
    global _chandra_available
    if _chandra_available is not None:
        return _chandra_available
    try:
        from chandra.input import load_file
        from chandra.model.vllm import generate_vllm
        from chandra.model.hf import load_model as hf_load_model
        from chandra.output import parse_markdown, parse_html
        _chandra_available = True
    except ImportError:
        _chandra_available = False
    return _chandra_available


def _get_hf_model():
    global _chandra_model, _hf_processor
    if _chandra_model is None:
        from chandra.model.hf import load_model
        _chandra_model = load_model()
        _hf_processor = _chandra_model.processor
    return _chandra_model


# ─────────────────────────────────────────────────────────────────────────────
# Core async wrappers
# ─────────────────────────────────────────────────────────────────────────────

def _ocr_sync_vllm(image_paths: list[str], output_format: str = "markdown") -> ChandraResult:
    """Run Chandra OCR via vLLM (sync). Returns markdown + HTML + raw."""
    from chandra.input import load_file
    from chandra.model.vllm import generate_vllm
    from chandra.model.schema import BatchInputItem
    from chandra.output import parse_markdown, parse_html, extract_images

    batch: list[BatchInputItem] = []
    pil_images: list = []

    for path in image_paths:
        images = load_file(path, {})
        for img in images:
            batch.append(BatchInputItem(image=img, prompt_type="ocr_layout"))
            pil_images.append(img)

    if not batch:
        return ChandraResult(
            markdown="", html="", raw="", token_count=0, page_count=0,
            source="chandra_vllm", error=True, error_message="No images loaded"
        )

    results = generate_vllm(batch)

    if not results or all(r.error for r in results):
        return ChandraResult(
            markdown="", html="", raw="", token_count=0, page_count=len(batch),
            source="chandra_vllm", error=True,
            error_message="All vLLM generations failed"
        )

    # Aggregate results
    all_html_parts: list[str] = []
    all_markdown_parts: list[str] = []
    total_tokens = 0
    images: dict = {}

    for res, pil_img in zip(results, pil_images):
        if res.error:
            continue
        raw = res.raw or ""
        total_tokens += res.token_count

        # Parse HTML layout
        html_out = parse_html(raw, include_headers_footers=False, include_images=True)
        markdown_out = parse_markdown(raw, include_headers_footers=False, include_images=True)

        # Extract embedded images
        extracted = extract_images(raw, [], pil_img)
        for k, v in extracted.items():
            images[k] = v

        all_html_parts.append(html_out)
        all_markdown_parts.append(markdown_out)

    return ChandraResult(
        markdown="\n\n".join(all_markdown_parts),
        html="\n\n".join(all_html_parts),
        raw=results[0].raw if results else "",
        token_count=total_tokens,
        page_count=len(batch),
        source="chandra_vllm",
        error=False,
    )


def _ocr_sync_hf(image_paths: list[str]) -> ChandraResult:
    """Run Chandra OCR via HuggingFace (sync). Returns markdown + HTML + raw."""
    from chandra.input import load_file
    from chandra.model.hf import generate_hf
    from chandra.model.schema import BatchInputItem
    from chandra.output import parse_markdown, parse_html, extract_images

    model = _get_hf_model()
    batch: list[BatchInputItem] = []
    pil_images: list = []

    for path in image_paths:
        images = load_file(path, {})
        for img in images:
            batch.append(BatchInputItem(image=img, prompt_type="ocr_layout"))
            pil_images.append(img)

    if not batch:
        return ChandraResult(
            markdown="", html="", raw="", token_count=0, page_count=0,
            source="chandra_hf", error=True, error_message="No images loaded"
        )

    results = generate_hf(batch, model)

    all_html_parts: list[str] = []
    all_markdown_parts: list[str] = []
    total_tokens = 0
    images: dict = {}

    for res, pil_img in zip(results, pil_images):
        if res.error:
            continue
        raw = res.raw or ""
        total_tokens += res.token_count
        html_out = parse_html(raw, include_headers_footers=False, include_images=True)
        markdown_out = parse_markdown(raw, include_headers_footers=False, include_images=True)
        extracted = extract_images(raw, [], pil_img)
        for k, v in extracted.items():
            images[k] = v
        all_html_parts.append(html_out)
        all_markdown_parts.append(markdown_out)

    return ChandraResult(
        markdown="\n\n".join(all_markdown_parts),
        html="\n\n".join(all_html_parts),
        raw=results[0].raw if results else "",
        token_count=total_tokens,
        page_count=len(batch),
        source="chandra_hf",
        error=False,
    )


def _ocr_sync_pytesseract(image_paths: list[str], lang: str = "eng+ind") -> ChandraResult:
    """Fallback to pytesseract when Chandra is unavailable."""
    import pytesseract
    from PIL import Image
    import filetype

    parts: list[str] = []
    total_tokens = 0
    page_count = 0

    for path in image_paths:
        file_type = filetype.guess(path)
        if file_type and file_type.extension == "pdf":
            import pypdfium2
            doc = pypdfium2.PdfDocument(path)
            doc.init_forms()
            for page_idx in range(len(doc)):
                page_obj = doc[page_idx]
                scale = 200 / 72
                pil_img = page_obj.render(scale=scale).to_pil().convert("RGB")
                page_count += 1
                text = pytesseract.image_to_string(pil_img, lang=lang)
                parts.append(f"--- Page {page_count} (OCR) ---\n{text.strip()}")
                total_tokens += len(text) // 4
            doc.close()
        else:
            pil_img = Image.open(path).convert("RGB")
            page_count += 1
            text = pytesseract.image_to_string(pil_img, lang=lang)
            parts.append(f"--- Page {page_count} (OCR) ---\n{text.strip()}")
            total_tokens += len(text) // 4

    return ChandraResult(
        markdown="\n\n".join(parts),
        html="",
        raw="\n\n".join(parts),
        token_count=total_tokens,
        page_count=page_count,
        source="pytesseract",
        error=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public async API
# ─────────────────────────────────────────────────────────────────────────────

async def chandra_ocr_image(
    path: str,
    method: str = "vllm",
    lang: str = "eng+ind",
) -> ChandraResult:
    """OCR a single image file with Chandra.

    Args:
        path: Path to image file (PNG, JPEG, WebP, etc.)
        method: "vllm" (default) or "hf" (HuggingFace) or "tesseract" (fallback)
        lang: Tesseract language code (used for tesseract fallback)

    Returns:
        ChandraResult with markdown, html, raw, token_count, page_count, source
    """
    p = Path(path).expanduser()
    if not p.exists():
        return ChandraResult(
            markdown="", html="", raw="", token_count=0, page_count=0,
            source=method, error=True, error_message=f"File not found: {path}"
        )

    def run():
        if method == "vllm":
            if not _check_chandra_available():
                logger.warning("Chandra not available, falling back to pytesseract")
                return _ocr_sync_pytesseract([str(p)], lang=lang)
            try:
                return _ocr_sync_vllm([str(p)])
            except Exception as e:
                logger.error(f"Chandra vLLM failed: {e}, falling back to pytesseract")
                return _ocr_sync_pytesseract([str(p)], lang=lang)
        elif method == "hf":
            if not _check_chandra_available():
                return _ocr_sync_pytesseract([str(p)], lang=lang)
            try:
                return _ocr_sync_hf([str(p)])
            except Exception as e:
                logger.error(f"Chandra HF failed: {e}, falling back to pytesseract")
                return _ocr_sync_pytesseract([str(p)], lang=lang)
        else:
            return _ocr_sync_pytesseract([str(p)], lang=lang)

    return await asyncio.to_thread(run)


async def chandra_ocr_pdf(
    path: str,
    pages: str = "all",
    method: str = "vllm",
    lang: str = "eng+ind",
) -> ChandraResult:
    """OCR a PDF (multi-page) with Chandra.

    Args:
        path: Path to PDF file
        pages: Page range string ("all", "1-5", "1,3,5", etc.)
        method: "vllm" (default), "hf", or "tesseract"
        lang: Tesseract language code (used for tesseract fallback)

    Returns:
        ChandraResult with markdown, html, raw, token_count, page_count, source
    """
    p = Path(path).expanduser()
    if not p.exists():
        return ChandraResult(
            markdown="", html="", raw="", token_count=0, page_count=0,
            source=method, error=True, error_message=f"File not found: {path}"
        )

    def _parse_page_range(pages_str: str, total: int) -> list[int]:
        """Parse page range string into list of 0-indexed page numbers."""
        if pages_str == "all":
            return list(range(total))
        result = []
        for part in pages_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                start = max(1, int(start))
                end = min(total, int(end))
                result.extend(range(start - 1, end))
            else:
                n = int(part)
                if 1 <= n <= total:
                    result.append(n - 1)
        return result

    def run():
        page_nums = _parse_page_range(pages, len(pil_images)) if pages != "all" else []

        if method == "tesseract":
            # Use pytesseract directly for PDF pages
            import pytesseract, pypdfium2

            doc = pypdfium2.PdfDocument(str(p))
            doc.init_forms()
            total = len(doc)
            page_nums_used = page_nums if page_nums else list(range(total))
            parts: list[str] = []
            total_tokens = 0

            for i in page_nums_used:
                if i >= total:
                    continue
                page_obj = doc[i]
                scale = 200 / 72
                pil_img = page_obj.render(scale=scale).to_pil().convert("RGB")
                text = pytesseract.image_to_string(pil_img, lang=lang)
                parts.append(f"--- Page {i + 1} (OCR) ---\n{text.strip()}")
                total_tokens += len(text) // 4
            doc.close()

            return ChandraResult(
                markdown="\n\n".join(parts),
                html="",
                raw="\n\n".join(parts),
                token_count=total_tokens,
                page_count=len(page_nums_used),
                source="pytesseract",
                error=False,
            )

        # vllm / hf methods need Chandra
        if not _check_chandra_available():
            return ChandraResult(
                markdown="", html="", raw="", token_count=0, page_count=0,
                source=method, error=True, error_message="Chandra OCR not installed. Run: pip install chandra-ocr"
            )

        try:
            from chandra.input import load_pdf_images, parse_range_str
            from chandra.model.vllm import generate_vllm
            from chandra.model.hf import generate_hf
            from chandra.model.schema import BatchInputItem
            from chandra.output import parse_markdown, parse_html, extract_images

            pil_images = load_pdf_images(str(p), page_nums if page_nums else None)

            if not pil_images:
                return ChandraResult(
                    markdown="", html="", raw="", token_count=0, page_count=0,
                    source=method, error=True, error_message="No pages in PDF"
                )

            # Save to temp PNG files for Chandra
            import tempfile, os as _os
            temp_files: list[str] = []
            for img in pil_images:
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                img.save(tmp.name, format="PNG")
                temp_files.append(tmp.name)
                tmp.close()

            try:
                if method == "vllm":
                    result = _ocr_sync_vllm(temp_files)
                else:
                    result = _ocr_sync_hf(temp_files)
            finally:
                for tf in temp_files:
                    _os.unlink(tf)

            result.page_count = len(pil_images)
            return result

        except Exception as e:
            logger.error(f"Chandra PDF OCR failed: {e}")
            return ChandraResult(
                markdown="", html="", raw="", token_count=0, page_count=0,
                source=method, error=True, error_message=str(e)
            )

    return await asyncio.to_thread(run)


async def chandra_ocr_bytes(
    image_bytes: bytes,
    method: str = "vllm",
    output_format: str = "markdown",
    lang: str = "eng+ind",
) -> ChandraResult:
    """OCR from raw image bytes (e.g. screenshot, uploaded photo).

    Args:
        image_bytes: Raw PNG/JPEG bytes
        method: "vllm", "hf", or "tesseract"
        output_format: "markdown" (default) or "html"
        lang: Tesseract language code (fallback)

    Returns:
        ChandraResult
    """
    import tempfile, os as _os

    # Write bytes to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.write(image_bytes)
    tmp_path = tmp.name
    tmp.close()

    try:
        return await chandra_ocr_image(tmp_path, method=method, lang=lang)
    finally:
        _os.unlink(tmp_path)


# ─────────────────────────────────────────────────────────────────────────────
# vLLM server management helpers
# ─────────────────────────────────────────────────────────────────────────────

def is_vllm_server_available() -> bool:
    """Check if a vLLM server is reachable at the configured address."""
    try:
        from chandra.settings import settings
        import requests
        resp = requests.get(
            f"{settings.VLLM_API_BASE}/models",
            timeout=5,
            headers={"Authorization": f"Bearer {settings.VLLM_API_KEY}"}
        )
        return resp.status_code == 200
    except Exception:
        return False


def get_chandra_status() -> dict:
    """Return a dict describing Chandra availability and configured backend."""
    vllm_ok = is_vllm_server_available()
    chandra_ok = _check_chandra_available()

    return {
        "chandra_installed": chandra_ok,
        "vllm_server_available": vllm_ok,
        "vllm_api_base": os.getenv("VLLM_API_BASE", "http://localhost:8000/v1"),
        "hf_available": chandra_ok,  # HF needs torch/transformers
        "recommended": "vllm" if (chandra_ok and vllm_ok) else "tesseract",
    }