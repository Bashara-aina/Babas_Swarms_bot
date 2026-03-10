"""arxiv.py — Academic research tool for Legion.

Search arXiv, download papers, extract text, cross-reference with code.
Supports WorkerNet paper analysis for the POPW protocol.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus

import aiohttp

logger = logging.getLogger(__name__)

PAPERS_DIR = Path(__file__).parent.parent / "papers"
PAPERS_DIR.mkdir(exist_ok=True)

# ── WorkerNet core papers ────────────────────────────────────────────────────

WORKERNET_PAPERS = {
    "kendall2018": {
        "query": "Multi-Task Learning Using Uncertainty to Weigh Losses Kendall 2018",
        "arxiv_id": "1705.07115",
        "implements": ["MultiTaskLoss", "log_var_det", "log_var_pose", "log_var_act"],
        "key_equation": "L = sum_t [exp(-s_t) * L_t + s_t]",
    },
    "lin2017": {
        "query": "Focal Loss Dense Object Detection RetinaNet Lin 2017",
        "arxiv_id": "1708.02002",
        "implements": ["FocalLoss", "DetectionHead"],
        "key_equation": "FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)",
    },
    "feng2018": {
        "query": "Wing Loss Robust Facial Landmark Localisation Feng 2018",
        "arxiv_id": "1711.06753",
        "implements": ["WingLoss"],
        "key_equation": "wing(x) = w*ln(1 + |x|/epsilon) if |x| < w else |x| - C",
    },
    "cui2019": {
        "query": "Class-Balanced Loss Effective Number of Samples Cui 2019",
        "arxiv_id": "1901.05555",
        "implements": ["ClassBalancedFocalLoss"],
        "key_equation": "E_n = (1 - beta^n) / (1 - beta)",
    },
    "perez2018": {
        "query": "FiLM Visual Reasoning General Conditioning Layer Perez 2018",
        "arxiv_id": "1709.07871",
        "implements": ["PoseFiLMModule"],
        "key_equation": "FiLM(F|gamma,beta) = gamma * F + beta",
    },
    "ikea_asm": {
        "query": "IKEA Assembly Dataset Multi-Task Learning action recognition",
        "arxiv_id": "2007.09812",
        "implements": ["IKEAMultiTaskDataset"],
        "key_equation": "N/A - dataset paper",
    },
}


# ── arXiv API ────────────────────────────────────────────────────────────────

async def search_arxiv(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search arXiv API. Returns list of {title, authors, abstract, arxiv_id, pdf_url, published}."""
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={quote_plus(query)}&start=0&max_results={max_results}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            xml_text = await resp.text()

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    results = []

    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        summary_el = entry.find("atom:summary", ns)
        published_el = entry.find("atom:published", ns)
        id_el = entry.find("atom:id", ns)

        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""
        abstract = (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else ""
        published = (published_el.text or "")[:10] if published_el is not None else ""

        # Extract arxiv_id from URL
        raw_id = (id_el.text or "") if id_el is not None else ""
        arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id

        # Authors
        authors = []
        for author_el in entry.findall("atom:author", ns):
            name_el = author_el.find("atom:name", ns)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        # PDF link
        pdf_url = ""
        for link_el in entry.findall("atom:link", ns):
            if link_el.get("title") == "pdf":
                pdf_url = link_el.get("href", "")
                break
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

        results.append({
            "title": title,
            "authors": ", ".join(authors[:5]) + ("..." if len(authors) > 5 else ""),
            "abstract": abstract[:500],
            "arxiv_id": arxiv_id,
            "pdf_url": pdf_url,
            "published": published,
        })

    return results


async def download_paper(arxiv_id: str) -> str:
    """Download PDF to ~/swarm-bot/papers/{arxiv_id}.pdf. Returns local path."""
    clean_id = arxiv_id.replace("/", "_")
    pdf_path = PAPERS_DIR / f"{clean_id}.pdf"

    if pdf_path.exists():
        logger.info("Paper %s already downloaded", arxiv_id)
        return str(pdf_path)

    url = f"https://arxiv.org/pdf/{arxiv_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Download failed: HTTP {resp.status} for {url}")
            content = await resp.read()

    pdf_path.write_bytes(content)
    logger.info("Downloaded paper %s → %s (%d KB)", arxiv_id, pdf_path, len(content) // 1024)
    return str(pdf_path)


def extract_paper_text(pdf_path: str, max_chars: int = 8000) -> str:
    """Extract text from PDF using pdfplumber. Returns first max_chars."""
    try:
        import pdfplumber
    except ImportError:
        return "(pdfplumber not installed — run: pip install pdfplumber)"

    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                if sum(len(p) for p in text_parts) >= max_chars:
                    break
    except Exception as e:
        return f"PDF extraction error: {e}"

    full_text = "\n\n".join(text_parts)
    return full_text[:max_chars]


async def analyze_paper(text: str, question: str = "") -> str:
    """Send paper text to debug agent for structured professor-style analysis."""
    from llm_client import chat

    prompt = (
        "Analyze this research paper section with academic rigor:\n"
        "1. Core problem statement\n"
        "2. Key methodology / algorithm (with equations if present)\n"
        "3. Datasets used and evaluation metrics\n"
        "4. Main results and claims\n"
        "5. Limitations acknowledged by authors\n"
        "6. Open questions / future work\n"
    )
    if question:
        prompt += f"7. Answer this specific question: {question}\n"

    prompt += f"\nPaper text:\n{text[:6000]}"

    result, model = await chat(prompt, agent_key="debug")
    return result


async def analyze_codebase_vs_paper(
    code_files: list[str], paper_text: str
) -> str:
    """Cross-reference code files against paper methodology."""
    from llm_client import chat

    # Extract class/function names from code
    code_summary_parts = []
    for fpath in code_files:
        try:
            content = Path(fpath).read_text(errors="replace")
            # Extract class and function definitions
            classes = re.findall(r"class\s+(\w+)", content)
            funcs = re.findall(r"def\s+(\w+)", content)
            imports = re.findall(r"^(?:from|import)\s+(.+)$", content, re.MULTILINE)
            code_summary_parts.append(
                f"File: {Path(fpath).name}\n"
                f"  Classes: {', '.join(classes[:20])}\n"
                f"  Functions: {', '.join(funcs[:30])}\n"
                f"  Key imports: {', '.join(imports[:10])}\n"
            )
        except Exception as e:
            code_summary_parts.append(f"File: {fpath} — error reading: {e}")

    code_summary = "\n".join(code_summary_parts)

    prompt = (
        "Cross-reference this codebase against the paper methodology.\n\n"
        "CODE STRUCTURE:\n" + code_summary[:3000] + "\n\n"
        "PAPER METHODOLOGY:\n" + paper_text[:3000] + "\n\n"
        "For each paper equation/algorithm, identify:\n"
        "- Which class/function implements it\n"
        "- Any differences from the paper\n"
        "- Missing implementations\n"
    )

    result, _ = await chat(prompt, agent_key="debug")
    return result


# ── Benchmark monitoring ────────────────────────────────────────────────────

async def monitor_benchmark(
    dataset_name: str = "IKEA ASM",
    your_metrics: Optional[dict[str, float]] = None,
) -> str:
    """Search arXiv for new papers citing the dataset, compare metrics."""
    if your_metrics is None:
        your_metrics = {"act_accuracy": 0.6046}

    papers = await search_arxiv(f"{dataset_name} action recognition", max_results=10)

    from llm_client import chat

    metrics_str = ", ".join(f"{k}: {v}" for k, v in your_metrics.items())
    papers_str = "\n\n".join(
        f"Title: {p['title']}\nPublished: {p['published']}\nAbstract: {p['abstract'][:300]}"
        for p in papers[:5]
    )

    prompt = (
        f"Review these recent papers on {dataset_name} benchmark.\n"
        f"My current metrics: {metrics_str}\n\n"
        f"Papers:\n{papers_str}\n\n"
        "For each paper that reports results on this dataset:\n"
        "1. What metrics do they report?\n"
        "2. Is their performance higher than mine?\n"
        "3. What technique gives them the advantage?\n"
        "If no new SOTA found, say so."
    )
    result, _ = await chat(prompt, agent_key="analyst")
    return result
