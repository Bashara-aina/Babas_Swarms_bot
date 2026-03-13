"""WAJAR_WATCH — pdf_extractor: download PDFs and extract regulation constants via LLM."""
from __future__ import annotations

import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_TEXT_CHARS = 8000

# LLM system prompt for extraction — embedded verbatim per spec
_EXTRACTION_PROMPT = """You are an expert in Indonesian labor law and tax regulation, specializing \
in BPJS Ketenagakerjaan, BPJS Kesehatan, and PPh 21.

Extract ALL numerical regulatory constants from the provided document text.
Return ONLY a valid JSON array (no markdown, no explanation).

Each item must have exactly these fields:
{
  "constant_name": string,    // e.g. "bpjs_jp_wage_cap"
  "value": number,            // numeric only, no Rp symbol
  "unit": string,             // "rupiah_per_month"|"rate_decimal"|"rupiah_annual"
  "effective_date": string,   // "YYYY-MM-DD" or "unknown"
  "legal_basis": string,      // e.g. "PP 45/2015 Pasal 6"
  "verbatim_quote": string,   // exact sentence from document
  "confidence": string,       // "HIGH"|"MEDIUM"|"LOW"
  "calculation_shown": string|null  // e.g. "10547400 x 1.0511 = 11086372"
}

Rules:
- Never hallucinate regulation numbers. Only what is explicitly in the text.
- Distinguish: proposed vs enacted vs in-effect
- A rate (0.01, 0.02 etc) must have confidence="LOW" unless the document \
explicitly states a NEW value different from the known current value
- If no relevant constants found, return []
- Rupiah values: output as integer (e.g. 11086300, not 11_086_300)"""


@dataclass
class ExtractedConstant:
    constant_name: str
    value: float
    unit: str  # "rupiah_per_month" | "rate_decimal" | "rupiah_annual"
    effective_date: str  # "YYYY-MM-DD" or "unknown"
    legal_basis: str
    verbatim_quote: str  # exact sentence from document
    confidence: str  # "HIGH" | "MEDIUM" | "LOW"
    calculation_shown: str | None
    source_url: str
    extracted_at: str  # ISO datetime string


def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfminer.six."""
    from pdfminer.high_level import extract_text

    return extract_text(io.BytesIO(pdf_bytes))


def _parse_llm_response(response_text: str, pdf_url: str) -> list[ExtractedConstant]:
    """Parse LLM JSON response into ExtractedConstant list."""
    # Try to extract JSON from the response (handle markdown wrapping)
    text = response_text.strip()
    if text.startswith("```"):
        # Strip markdown code block
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Find the JSON array
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        logger.warning("No JSON array found in LLM response")
        return []

    try:
        items = json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        logger.error("JSON parse error: %s", e)
        return []

    now_iso = datetime.now(timezone.utc).isoformat()
    results = []
    for item in items:
        try:
            results.append(
                ExtractedConstant(
                    constant_name=str(item.get("constant_name", "")),
                    value=float(item.get("value", 0)),
                    unit=str(item.get("unit", "unknown")),
                    effective_date=str(item.get("effective_date", "unknown")),
                    legal_basis=str(item.get("legal_basis", "")),
                    verbatim_quote=str(item.get("verbatim_quote", "")),
                    confidence=str(item.get("confidence", "LOW")),
                    calculation_shown=item.get("calculation_shown"),
                    source_url=pdf_url,
                    extracted_at=now_iso,
                )
            )
        except (TypeError, ValueError) as e:
            logger.warning("Skipping malformed item: %s (%s)", item, e)

    return results


async def extract_from_pdf(pdf_url: str) -> list[ExtractedConstant]:
    """Download PDF, extract text, run LLM analysis. Return constants."""
    # Download PDF
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(pdf_url, follow_redirects=True)
        resp.raise_for_status()

        if len(resp.content) > MAX_PDF_SIZE:
            logger.warning("PDF too large (%d bytes): %s", len(resp.content), pdf_url)
            return []

    # Extract text
    try:
        raw_text = _extract_text_from_pdf_bytes(resp.content)
    except Exception as e:
        logger.error("PDF text extraction failed for %s: %s", pdf_url, e)
        return []

    if not raw_text.strip():
        logger.warning("No text extracted from PDF: %s", pdf_url)
        return []

    # Truncate to max chars
    doc_text = raw_text[:MAX_TEXT_CHARS]

    # Build the task prompt for llm_client.chat()
    task = (
        f"{_EXTRACTION_PROMPT}\n\n"
        f"Document text:\n{doc_text}"
    )

    # Call LLM via the public chat() interface — uses regulation_watcher fallback chain
    try:
        from llm_client import chat

        response_text, model_used = await chat(
            task=task,
            agent_key="regulation_watcher",
        )
        logger.info("PDF extraction used model: %s for %s", model_used, pdf_url)
    except Exception as e:
        logger.error("LLM call failed for PDF %s: %s", pdf_url, e)
        return []

    # Parse the response
    return _parse_llm_response(response_text, pdf_url)
