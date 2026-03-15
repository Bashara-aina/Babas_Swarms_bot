"""SecurityGuard — input validation, prompt injection detection, PII redaction.

Defense layers:
1. Prompt injection pattern detection
2. PII detection and redaction in inputs/outputs
3. Credential/secret pattern detection
4. Content length limits

Does NOT log user message content (privacy requirement from CLAUDE.md).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum allowed input length (characters)
MAX_INPUT_LENGTH = 50_000


@dataclass
class ValidationResult:
    """Result of input validation."""

    valid: bool
    sanitized_input: str = ""
    warnings: List[str] = None
    blocked_reason: str = ""

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class ScanResult:
    """Compatibility result used by tests and higher-level callers."""

    blocked: bool
    risk_score: float
    sanitized_text: str
    reasons: List[str]


# Prompt injection patterns
_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|above)\s+(?:instructions?|prompts?|rules?)",
    r"system:?\s+you\s+are\s+now",
    r"forget\s+(everything|all\s+previous)",
    r"new\s+instructions?:",
    r"</prompt>",
    r"<\|im_end\|>",
    r"<\|endoftext\|>",
    r"SUDO\s+MODE",
    r"you\s+are\s+now\s+in\s+(jailbreak|unrestricted|DAN)\s+mode",
    r"override\s+(all\s+)?safety",
    r"act\s+as\s+if\s+you\s+have\s+no\s+(restrictions?|limits?|rules?)",
    r"ignore\s+(?:the\s+)?(?:above|previous|system)\b",
]

# PII patterns for redaction
_PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(?:\+62|0)\d{9,12}\b",  # Indonesian phone numbers
    "cc_number": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "nik": r"\b\d{16}\b",  # Indonesian NIK (16 digits)
    "npwp": r"\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b",  # Indonesian NPWP
}

# Credential patterns
_CREDENTIAL_PATTERNS = [
    r"(?:api[_-]?key|token|secret|password|pwd)\s*[=:]\s*['\"][A-Za-z0-9/+=]{20,}['\"]",
    r"(?:api[_-]?key|token|secret|password|pwd|secretkey)\s*[=:]\s*[A-Za-z0-9_\-]{6,}",
    r"sk-[A-Za-z0-9\-_]{8,}",
    r"sk-[A-Za-z0-9]{32,}",  # OpenAI API key
    r"sk-ant-[A-Za-z0-9-]{40,}",  # Anthropic API key
    r"gsk_[A-Za-z0-9]{40,}",  # Groq API key
    r"AIzaSy[A-Za-z0-9_-]{33}",  # Google API key
    r"ghp_[A-Za-z0-9]{36}",  # GitHub PAT
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
]

_DANGEROUS_EXEC_PATTERNS = [
    re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\};:"),  # fork bomb
    re.compile(r"\b(drop\s+table|delete\s+from|truncate\s+table)\b", re.IGNORECASE),
]


class SecurityGuard:
    """Security layer for input/output validation.

    Detects prompt injection, redacts PII, and blocks credential leaks.
    Designed for the Telegram bot security boundary.
    """

    def __init__(
        self,
        enable_pii_redaction: bool = True,
        enable_injection_detection: bool = True,
        max_input_length: int = MAX_INPUT_LENGTH,
    ) -> None:
        self.enable_pii = enable_pii_redaction
        self.enable_injection = enable_injection_detection
        self.max_input_length = max_input_length
        self._injection_compiled = [
            re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS
        ]
        self._credential_compiled = [
            re.compile(p) for p in _CREDENTIAL_PATTERNS
        ]
        self._blocked_count = 0
        self._scanned_count = 0

    def validate_input(self, user_input: str) -> ValidationResult:
        """Validate and sanitize user input.

        Args:
            user_input: Raw input from Telegram message.

        Returns:
            ValidationResult with validity flag and sanitized text.
        """
        self._scanned_count += 1
        warnings: List[str] = []

        # Check length
        if len(user_input) > self.max_input_length:
            self._blocked_count += 1
            return ValidationResult(
                valid=False,
                blocked_reason=f"Input too long ({len(user_input)} chars, max {self.max_input_length})",
            )

        # Check prompt injection
        if self.enable_injection:
            injection = self._detect_injection(user_input)
            if injection:
                self._blocked_count += 1
                logger.warning("Prompt injection blocked: %s", injection)
                return ValidationResult(
                    valid=False,
                    blocked_reason="Potential prompt injection detected",
                )

        # Sanitize PII (in-place redaction)
        sanitized = user_input
        if self.enable_pii:
            sanitized, pii_warnings = self._redact_pii(user_input)
            warnings.extend(pii_warnings)

        return ValidationResult(
            valid=True,
            sanitized_input=sanitized,
            warnings=warnings,
        )

    def scan(self, text: str) -> ScanResult:
        """Scan text and return a risk-scored security decision.

        This wrapper preserves compatibility with older call-sites/tests expecting
        `.scan()` with fields: blocked, risk_score, sanitized_text.
        """
        validation = self.validate_input(text)
        sanitized = validation.sanitized_input if validation.valid else text
        reasons: list[str] = list(validation.warnings)
        risk = 0.0

        if not validation.valid:
            reasons.append(validation.blocked_reason)
            risk += 0.9

        if self._contains_credentials(text):
            sanitized = self._redact_credentials(sanitized)
            reasons.append("credential_detected")
            risk += 0.8

        for pattern in _DANGEROUS_EXEC_PATTERNS:
            if pattern.search(text):
                reasons.append("dangerous_payload")
                risk += 0.7
                break

        # If any PII survived initial validation path (e.g., validation blocked), redact here.
        if self.enable_pii:
            sanitized, pii_warnings = self._redact_pii(sanitized)
            reasons.extend(pii_warnings)
            if pii_warnings:
                risk += 0.2

        blocked = (not validation.valid) or risk >= 0.7
        risk = min(1.0, risk)
        return ScanResult(
            blocked=blocked,
            risk_score=round(risk, 3),
            sanitized_text=sanitized,
            reasons=reasons,
        )

    def filter_output(self, output: str) -> str:
        """Filter agent output before sending to user.

        Checks for credential leaks and optionally redacts PII.

        Args:
            output: Raw agent output.

        Returns:
            Sanitized output safe to send via Telegram.
        """
        # Check for credential leaks
        if self._contains_credentials(output):
            logger.error("Credentials detected in agent output — blocking")
            return (
                "<b>Response blocked:</b> Output contained what appears to be "
                "API keys or credentials. The response has been suppressed "
                "for security."
            )

        return output

    def _detect_injection(self, text: str) -> Optional[str]:
        """Detect prompt injection patterns.

        Returns the matched pattern name if injection detected, else None.
        """
        for i, pattern in enumerate(self._injection_compiled):
            if pattern.search(text):
                return f"pattern_{i}"
        return None

    def _redact_pii(self, text: str) -> tuple[str, List[str]]:
        """Redact PII patterns from text.

        Returns (redacted_text, list_of_warnings).
        """
        warnings = []
        result = text

        for pii_type, pattern in _PII_PATTERNS.items():
            matches = re.findall(pattern, result)
            if matches:
                result = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", result)
                warnings.append(f"PII redacted: {pii_type} ({len(matches)} instances)")

        return result, warnings

    def _contains_credentials(self, text: str) -> bool:
        """Check if text contains credential patterns."""
        for pattern in self._credential_compiled:
            if pattern.search(text):
                return True
        return False

    def _redact_credentials(self, text: str) -> str:
        redacted = text
        for pattern in self._credential_compiled:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted

    def get_stats(self) -> Dict[str, Any]:
        """Return security guard statistics."""
        return {
            "total_scanned": self._scanned_count,
            "total_blocked": self._blocked_count,
            "block_rate": (
                round(self._blocked_count / self._scanned_count, 3)
                if self._scanned_count > 0
                else 0.0
            ),
        }
