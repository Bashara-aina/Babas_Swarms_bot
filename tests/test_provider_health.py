"""Tests for core/reliability/provider_health.py"""

import time

from core.reliability.provider_health import (
    record_rate_limit,
    check_provider_health,
    get_healthy_provider,
    reset_provider_health,
    get_all_provider_status,
    _provider_health,
    _CIRCUIT_OPEN_DURATION,
    _RATE_LIMIT_COOLDOWN,
)


class TestProviderHealth:
    def setup_method(self):
        _provider_health.clear()

    def test_unknown_provider_is_healthy(self):
        assert check_provider_health("unknown") == "healthy"

    def test_record_rate_limit_marks_unavailable(self):
        record_rate_limit("openrouter")
        assert check_provider_health("openrouter") == "unavailable"

    def test_reset_provider_clears_health(self):
        record_rate_limit("openrouter")
        reset_provider_health("openrouter")
        assert "openrouter" not in _provider_health
        assert check_provider_health("openrouter") == "healthy"

    def test_get_healthy_provider_prefers_primary(self):
        result = get_healthy_provider("openrouter", "ollama")
        assert result == "openrouter"

    def test_get_healthy_provider_falls_back_when_unavailable(self):
        record_rate_limit("openrouter")
        result = get_healthy_provider("openrouter", "ollama")
        assert result == "ollama"

    def test_get_all_provider_status_returns_dict(self):
        record_rate_limit("openrouter")
        record_rate_limit("cerebras")
        status = get_all_provider_status()
        assert isinstance(status, dict)
        assert "openrouter" in status
        assert "cerebras" in status


class TestProviderHealthTiming:
    def setup_method(self):
        _provider_health.clear()

    def test_provider_becomes_degraded_after_circuit_open_duration(self):
        record_rate_limit("testprovider")
        # Set last_rate_limit to just before circuit-open duration expires
        _provider_health["testprovider"]["last_rate_limit"] = time.monotonic() - _CIRCUIT_OPEN_DURATION - 1
        status = check_provider_health("testprovider")
        assert status == "degraded"

    def test_provider_recovers_after_full_cooldown(self):
        record_rate_limit("testprovider")
        # Set last_rate_limit to after full cooldown
        _provider_health["testprovider"]["last_rate_limit"] = time.monotonic() - _CIRCUIT_OPEN_DURATION - _RATE_LIMIT_COOLDOWN - 1
        status = check_provider_health("testprovider")
        assert status == "healthy"
        assert "testprovider" not in _provider_health


class TestProviderHealthEdgeCases:
    def setup_method(self):
        _provider_health.clear()

    def test_multiple_rate_limits_for_same_provider(self):
        record_rate_limit("testprovider")
        first_check = check_provider_health("testprovider")
        assert first_check == "unavailable"
        # Second record should update timestamp
        record_rate_limit("testprovider")
        second_check = check_provider_health("testprovider")
        assert second_check == "unavailable"

    def test_get_healthy_provider_with_none_fallback(self):
        result = get_healthy_provider("unknown", "ollama")
        assert result == "unknown"

    def test_empty_provider_name(self):
        assert check_provider_health("") == "healthy"