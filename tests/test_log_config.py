"""Tests for log redaction — ensures API keys never appear in logs."""
import logging
import pytest
from core.log_config import RedactingFormatter


class TestRedactingFormatter:
    @pytest.fixture
    def formatter(self):
        return RedactingFormatter()

    def _format(self, formatter, message):
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg=message, args=(), exc_info=None
        )
        return formatter.format(record)

    def test_groq_api_key_redacted(self, formatter):
        result = self._format(formatter, "Error with key sk-abcdefghij1234567890xyz")
        assert "sk-abcdefghij" not in result
        assert "[REDACTED]" in result

    def test_telegram_token_redacted(self, formatter):
        result = self._format(formatter, "Token: bot123456789:ABCDefghIJKlmNOPqrsTUVwxyz1234567")
        assert "ABCDefghIJKlmNOPqrsTUVwxyz" not in result

    def test_safe_message_unchanged(self, formatter):
        msg = "User sent: write a python function"
        result = self._format(formatter, msg)
        assert "write a python function" in result

    def test_google_api_key_redacted(self, formatter):
        result = self._format(formatter, "key=AIzaSyB1234567890abcdefghijklmnopqrstuvw")
        assert "AIzaSy" not in result
