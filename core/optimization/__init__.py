"""Optimization module for cost tracking and feedback-driven learning.

This module provides two core components:

- **UsageTracker** (`usage_tracker.py`): Tracks per-model token usage and
  estimated API costs. Supports Redis backend with in-memory fallback.
  Emits alerts when approaching daily rate limits.

- **FeedbackLearner** (`feedback_learner.py`): Collects user ratings
  (thumbs up/down) for agent responses. Adjusts agent selection weights,
  surfaces worst-performing agents in stats, and evicts negative-feedback
  cache entries.

Both components use a singleton pattern via `get_tracker()` and
`get_learner()` respectively.
"""

from __future__ import annotations
