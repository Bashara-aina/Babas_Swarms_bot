import contextlib
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _check_markitdown() -> bool:
    import importlib.util
    available = importlib.util.find_spec("markitdown") is not None
    if not available:
        logger.warning("markitdown not installed. Run: pip install 'markitdown[all]'")
    return available


MARKITDOWN_AVAILABLE = _check_markitdown()


async def parse_file(file_path: str | Path, use_llm_for_images: bool = False) -> dict:
    file_path = Path(file_path)
    if not file_path.exists():
        return {"markdown": "", "title": "", "file_type": "", "char_count": 0, "error": f"File not found: {file_path}"}

    file_type = file_path.suffix.lower()

    if MARKITDOWN_AVAILABLE:
        try:
            from markitdown import MarkItDown

            md = MarkItDown(llm_client=None, llm_model=None)
            result = md.convert(str(file_path))
            markdown = result.text_content
            title = result.title or file_path.stem
            logger.info(f"Parsed {file_path.name}: {len(markdown)} chars via markitdown")
            return {"markdown": markdown, "title": title, "file_type": file_type, "char_count": len(markdown)}
        except Exception as e:
            logger.warning(f"markitdown failed for {file_path}: {e}. Trying fallback.")

    if file_type == ".pdf":
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            markdown = "\n\n".join(text_parts)
            return {"markdown": markdown, "title": file_path.stem, "file_type": ".pdf", "char_count": len(markdown)}
        except Exception as e:
            return {"markdown": "", "title": "", "file_type": file_type, "char_count": 0, "error": str(e)}

    return {
        "markdown": "",
        "title": "",
        "file_type": file_type,
        "char_count": 0,
        "error": f"Unsupported file type: {file_type}",
    }


async def parse_telegram_document(bot, file_id: str, save_dir: str = "/tmp/legion_docs") -> dict:
    os.makedirs(save_dir, exist_ok=True)
    try:
        file = await bot.get_file(file_id)
        filename = Path(file.file_path).name
        local_path = Path(save_dir) / filename
        await file.download_to_drive(local_path)
        logger.info(f"Downloaded Telegram file: {filename}")
        result = await parse_file(local_path)
        with contextlib.suppress(Exception):
            os.remove(local_path)
        return result
    except Exception as e:
        logger.error(f"Failed to download/parse Telegram file: {e}")
        return {"markdown": "", "title": "", "file_type": "", "char_count": 0, "error": str(e)}


SKILL_META = {
    "name": "doc_parser",
    "description": "Parse any document (PDF, DOCX, XLSX, PPTX, image) to Markdown.",
    "triggers": ["parse", "baca file", "ekstrak", "dokumen", "payslip", "upload"],
    "execute": parse_file,
    "requires_internet": False,
    "avg_latency_seconds": 3,
    "cost_tier": "free",
}
