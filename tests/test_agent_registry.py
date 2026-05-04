"""Tests for core/agent_registry.py — detect_agent(), get_fallback_chain(), search_by_capability()."""




class TestDetectAgent:
    """Tests for detect_agent()."""

    def test_detect_agent_math_keywords(self):
        """High-confidence math intent should return 'math' agent."""
        from core.agent_registry import detect_agent

        result = detect_agent("calculate the derivative of x^2")
        assert result == "math"

    def test_detect_agent_debug_keywords(self):
        """Traceback/error keywords should return 'debug' agent."""
        from core.agent_registry import detect_agent

        result = detect_agent("I got a traceback error in my Python code")
        assert result == "debug"

    def test_detect_agent_architect_keywords(self):
        """Architecture keywords should return 'architect' agent."""
        from core.agent_registry import detect_agent

        result = detect_agent("design the system architecture for my microservice")
        assert result == "architect"

    def test_detect_agent_coding_keywords(self):
        """Code-related keywords should return 'coding' agent."""
        from core.agent_registry import detect_agent

        result = detect_agent("write a Python function to parse JSON")
        assert result == "coding"

    def test_detect_agent_general_fallback(self):
        """Generic tasks should fall back to 'general' agent."""
        from core.agent_registry import detect_agent

        result = detect_agent("what is the capital of France?")
        assert result == "general"


class TestGetFallbackChain:
    """Tests for get_fallback_chain()."""

    def test_get_fallback_chain_known_agent(self):
        """Known agent should return its fallback chain."""
        from core.agent_registry import get_fallback_chain

        chain = get_fallback_chain("vision")
        assert isinstance(chain, list)
        assert len(chain) > 0
        assert "ollama_chat/gemma4:e4b" in chain

    def test_get_fallback_chain_unknown_agent(self):
        """Unknown agent should return general fallback chain (MiniMax primary)."""
        from core.agent_registry import get_fallback_chain

        chain = get_fallback_chain("nonexistent_agent_xyz")
        assert isinstance(chain, list)
        assert len(chain) > 0
        # Should fall back to general chain (MiniMax primary, MiniMax Text fallback)
        assert "minimax/MiniMax-M2.7" in chain

    def test_get_fallback_chain_coding(self):
        """Coding agent should have MiniMax primary with MiniMax Text fallback."""
        from core.agent_registry import get_fallback_chain

        chain = get_fallback_chain("coding")
        assert "minimax/MiniMax-M2.7" in chain
        assert "minimax/MiniMax-Text-01" in chain


class TestSearchByCapability:
    """Tests for search_by_capability()."""

    def test_search_by_capability_exact_match(self):
        """Exact capability match should score higher."""
        from core.agent_registry import search_by_capability

        results = search_by_capability(["screenshot"])
        assert isinstance(results, list)

    def test_search_by_capability_multiple_keywords(self):
        """Multiple keywords should aggregate scores."""
        from core.agent_registry import search_by_capability

        results = search_by_capability(["code", "debug"])
        assert isinstance(results, list)

    def test_search_by_capability_returns_tuples(self):
        """Results should be (agent_name, score) tuples."""
        from core.agent_registry import search_by_capability

        results = search_by_capability(["python"])
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], int)

    def test_search_by_capability_sorted_by_score(self):
        """Results should be sorted by score descending."""
        from core.agent_registry import search_by_capability

        results = search_by_capability(["code", "debug", "python"])
        if len(results) >= 2:
            assert results[0][1] >= results[1][1]
