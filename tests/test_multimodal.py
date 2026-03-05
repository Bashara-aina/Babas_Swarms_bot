# /home/newadmin/swarm-bot/tests/test_multimodal.py
"""Tests for multimodal_processor.py — run with: pytest tests/test_multimodal.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
import multimodal_processor


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_extract_pdf_missing_dep(monkeypatch):
    """Should raise RuntimeError if pypdf is not installed."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name in ("pypdf", "PyPDF2"):
            raise ImportError("mocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    with pytest.raises(RuntimeError, match="pypdf not installed"):
        multimodal_processor._extract_pdf_sync(b"")


def test_process_document_txt():
    content = b"Hello from a text file"
    text, label = run(multimodal_processor.process_document(content, "text/plain", "test.txt"))
    assert "Hello from a text file" in text
    assert label == "TXT"


def test_process_document_unsupported():
    text, label = run(multimodal_processor.process_document(b"data", "application/zip", "file.zip"))
    assert text == ""
    assert "Unsupported" in label


def test_max_context_chars_truncation():
    huge = b"A" * (multimodal_processor.MAX_CONTEXT_CHARS + 1000)
    text, label = run(multimodal_processor.process_document(huge, "text/plain", "big.txt"))
    assert len(text) <= multimodal_processor.MAX_CONTEXT_CHARS + 50  # small buffer for truncation msg
    assert "truncated" in text
