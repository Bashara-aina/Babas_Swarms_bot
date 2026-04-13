"""Tests for core/intent_router.py — intent classification."""

import pytest
from core.intent_router import Intent, classify_intent_fast, IntentResult


class TestClassifyIntentFast:
    """Tests for classify_intent_fast()."""

    def test_classify_computer_control(self):
        """Open/click/launch commands should be COMPUTER_CONTROL."""
        result = classify_intent_fast("open spotify and play music")
        assert result.intent == Intent.COMPUTER_CONTROL

    def test_classify_code_generation(self):
        """Write/implement commands should be CODE_GENERATION."""
        result = classify_intent_fast("write a Python function to sort a list")
        assert result.intent == Intent.CODE_GENERATION

    def test_classify_code_review(self):
        """Review/audit code commands should be CODE_REVIEW."""
        result = classify_intent_fast("review the code for security issues")
        assert result.intent == Intent.CODE_REVIEW

    def test_classify_web_research(self):
        """Research/explain queries should be WEB_RESEARCH."""
        result = classify_intent_fast("explain how transformers work")
        assert result.intent == Intent.WEB_RESEARCH

    def test_classify_web_scrape(self):
        """Scrape specific URL should be WEB_SCRAPE."""
        result = classify_intent_fast("scrape the pricing table from example.com")
        assert result.intent == Intent.WEB_SCRAPE

    def test_classify_memory_search(self):
        """Memory search queries should be MEMORY_SEARCH."""
        result = classify_intent_fast("what did I tell you about my project last week?")
        assert result.intent == Intent.MEMORY_SEARCH

    def test_classify_schedule_task(self):
        """Reminder/schedule queries should be SCHEDULE_TASK."""
        result = classify_intent_fast("remind me tomorrow at 9am about the meeting")
        assert result.intent == Intent.SCHEDULE_TASK

    def test_classify_translation(self):
        """Translation queries should be TRANSLATION."""
        result = classify_intent_fast("translate this to Indonesian")
        assert result.intent == Intent.TRANSLATION

    def test_classify_math_reasoning(self):
        """Math/calculation queries should be MATH_REASONING."""
        result = classify_intent_fast("calculate the eigenvalues of this matrix")
        assert result.intent == Intent.MATH_REASONING

    def test_classify_creative_write(self):
        """Creative writing queries should be CREATIVE_WRITE."""
        result = classify_intent_fast("write a short story about a robot")
        assert result.intent == Intent.CREATIVE_WRITE

    def test_classify_deep_reasoning(self):
        """Complex multi-step queries should be DEEP_REASONING."""
        result = classify_intent_fast(
            "analyze the trade-offs between microservices and monolith for a startup with limited resources"
        )
        assert result.intent == Intent.DEEP_REASONING

    def test_classify_casual_chat(self):
        """Casual conversation should be CASUAL_CHAT."""
        result = classify_intent_fast("how are you today?")
        assert result.intent == Intent.CASUAL_CHAT

    def test_classify_site_analysis(self):
        """Site analysis queries should be SITE_ANALYSIS."""
        result = classify_intent_fast("my rumahlabuh site feels slow, analyze it")
        assert result.intent == Intent.SITE_ANALYSIS

    def test_classify_email_read(self):
        """Read email queries should be EMAIL_READ."""
        result = classify_intent_fast("check my inbox for new emails")
        assert result.intent == Intent.EMAIL_READ

    def test_classify_file_operation(self):
        """File operations should be FILE_OPERATION."""
        result = classify_intent_fast("read the contents of readme.md")
        assert result.intent == Intent.FILE_OPERATION

    def test_classify_memory_store(self):
        """Remember/SAVE commands should be MEMORY_STORE."""
        result = classify_intent_fast("remember that I prefer dark mode")
        assert result.intent == Intent.MEMORY_STORE

    def test_classify_email_write(self):
        """Draft/send email commands should be EMAIL_WRITE."""
        result = classify_intent_fast("send an email to john@example.com saying hello")
        assert result.intent == Intent.EMAIL_WRITE

    def test_classify_database_audit(self):
        """Database operations should be DATABASE_AUDIT."""
        result = classify_intent_fast("check the supabase users table for duplicates")
        assert result.intent == Intent.DATABASE_AUDIT

    def test_classify_weather_query(self):
        """Weather queries should be WEATHER_QUERY."""
        result = classify_intent_fast("what's the weather like in Tokyo today?")
        assert result.intent == Intent.WEATHER_QUERY

    def test_classify_location_query(self):
        """Location queries should be LOCATION_QUERY."""
        result = classify_intent_fast("find good ramen restaurants near Shibuya")
        assert result.intent == Intent.LOCATION_QUERY

    def test_classify_data_analysis(self):
        """Data analysis queries should be DATA_ANALYSIS."""
        result = classify_intent_fast("run a data analysis on this CSV file")
        assert result.intent == Intent.DATA_ANALYSIS

    def test_classify_api_call(self):
        """External API calls should be API_CALL."""
        result = classify_intent_fast("call the GitHub API to list my repos")
        assert result.intent == Intent.API_CALL

    def test_classify_self_upgrade(self):
        """Self-upgrade queries should be SELF_UPGRADE."""
        result = classify_intent_fast("check what changed in the latest commit")
        assert result.intent == Intent.SELF_UPGRADE

    def test_classify_unknown_defaults_to_casual(self):
        """Unknown patterns should default to CASUAL_CHAT."""
        result = classify_intent_fast("asjdkfhaskjdhf")
        assert result.intent == Intent.CASUAL_CHAT

    def test_intent_result_structure(self):
        """Result should be an IntentResult with expected fields."""
        result = classify_intent_fast("hello")
        assert isinstance(result, IntentResult)
        assert hasattr(result, "intent")
        assert hasattr(result, "confidence")
        assert hasattr(result, "method")
        assert hasattr(result, "raw_message")
        assert hasattr(result, "needs_tools")
        assert hasattr(result, "needs_research")

    def test_confidence_range(self):
        """Confidence should be between 0 and 1."""
        result = classify_intent_fast("explain how transformers work")
        assert 0.0 <= result.confidence <= 1.0

    def test_method_is_pattern(self):
        """Fast classification should use 'pattern' method."""
        result = classify_intent_fast("write code")
        assert result.method == "pattern"


class TestBuildIntentHint:
    """Tests for build_intent_hint()."""

    def test_build_hint_high_confidence(self):
        """High confidence intent should produce hint."""
        from core.intent_router import build_intent_hint

        result = classify_intent_fast("write a Python function")
        hint = build_intent_hint(result)
        assert isinstance(hint, str)

    def test_build_hint_low_confidence_empty(self):
        """Low confidence should return empty hint."""
        from core.intent_router import build_intent_hint

        result = classify_intent_fast("hello")
        result = IntentResult(
            intent=Intent.CASUAL_CHAT,
            confidence=0.3,
            method="pattern",
            raw_message="hello",
        )
        hint = build_intent_hint(result)
        assert hint == ""
