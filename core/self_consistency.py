"""M2.7 Self-Consistency Verifier — multi-approach scoring for high-stakes decisions.

Solves the "single-path blind spot" problem: when you're confident in one approach
but haven't stress-tested alternatives. Generates 3 diverse candidate approaches,
then scores each on correctness × maintainability × risk × fit-to-project-scale.

High-stakes threshold: confidence < 80% → surface to user before proceeding.

Reference: M2.7 Full Capability Activation — Self-Consistency Verification (Section D3)
Original paper: "Self-Consistency Improves Chain of Thought Reasoning in Language Models" (ICLR 2023)
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import StrEnum

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class ApproachStrength(StrEnum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


@dataclass
class ScoredApproach:
    """A single candidate approach with multi-dimensional scoring."""

    approach_id: str
    title: str
    description: str
    correctness: float          # 0.0–1.0: does it solve the problem?
    maintainability: float      # 0.0–1.0: will future-you understand it?
    risk: float                 # 0.0–1.0: how likely to cause production issues?
    fit_to_project: float       # 0.0–1.0: does it match swarm-bot's async/aiogram/litellm architecture?
    overall_score: float = 0.0  # weighted product: correctness^0.3 * maintainability^0.25 * (1-risk)^0.25 * fit^0.2
    reasoning: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    recommended: bool = False

    def __post_init__(self) -> None:
        """Compute overall score and determine recommendation."""
        # Weight: correctness 30%, maintainability 25%, risk 25%, fit 20%
        # Risk is inverted (lower risk = higher score)
        self.overall_score = (
            (self.correctness ** 0.3)
            * (self.maintainability ** 0.25)
            * ((1 - self.risk) ** 0.25)
            * (self.fit_to_project ** 0.2)
        )
        self.recommended = self.overall_score >= 0.65


@dataclass
class SelfConsistencyVerdict:
    """Final verdict from multi-approach self-consistency check."""

    decision_topic: str
    approaches: list[ScoredApproach]
    winner: ScoredApproach | None
    confidence: float           # 0.0–1.0: how sure should we be?
    consensus_strength: float    # 0.0–1.0: how much did approaches agree?
    should_proceed: bool         # True if confidence >= 0.80
    concerns: list[str] = field(default_factory=list)
    recommendation: str = ""     # Human-readable one-line recommendation
    checked_at: str = field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()
    )

    def winning_approach_id(self) -> str | None:
        return self.winner.approach_id if self.winner else None


# ---------------------------------------------------------------------------
# Approach generators (project-aware)
# ---------------------------------------------------------------------------

_APPROACH_GENERATORS = {
    # Each generator returns (title, description) for a given decision topic
}


def register_approach_generator(category: str, generator):
    """Register a generator for a decision category.

    Generator signature: (topic: str, existing_context: str) -> list[tuple[title, description]]
    """
    _APPROACH_GENERATORS[category] = generator


# ---------------------------------------------------------------------------
# Default approach generator — 3 canonical approaches
# ---------------------------------------------------------------------------


def _default_3_approaches(topic: str, context: str) -> list[tuple[str, str]]:
    """Default: conservative, moderate, aggressive."""
    return [
        (
            f"Conservative: minimal change to existing {topic.split()[-1]}",
            f"Reuse existing patterns. Add thin compatibility layer. "
            f"Avoid refactoring. Suitable if {topic} is stable/production-critical."
        ),
        (
            "Moderate: clean integration with swarm-bot async architecture",
            f"Implement new {topic.split()[-1]} using aiosqlite/aiogram patterns already in codebase. "
            f"Rough consensus on structure from existing modules. "
            f"Medium risk, good maintainability."
        ),
        (
            "Aggressive: full replacement with modern patterns",
            "Drop legacy approach entirely. Use latest patterns from core/ modules. "
            "Highest risk, highest reward if the codebase is ready. "
            "Requires thorough testing."
        ),
    ]


# ---------------------------------------------------------------------------
# Self-Consistency Verifier
# ---------------------------------------------------------------------------


class SelfConsistencyVerifier:
    """Multi-approach self-consistency scoring for high-stakes decisions.

    Usage:
        verifier = SelfConsistencyVerifier("/home/newadmin/swarm-bot")

        # Before committing to a major decision:
        verdict = await verifier.verify_decision(
            topic="Add aiosqlite connection pool to BudgetManager",
            context="BudgetManager is accessed by 3 concurrent handlers on every /budget call",
            categories=["async", "database"],
        )

        if not verdict.should_proceed:
            # Surface to user
            print(f"⚠️ Confidence {verdict.confidence:.0%} — need human review")
            for concern in verdict.concerns:
                print(f"  {concern}")

        if verdict.winner:
            print(f"✅ Best approach: {verdict.winner.title} ({verdict.winner.overall_score:.2f})")
    """

    def __init__(self, project_root: str | None = None) -> None:
        from pathlib import Path
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def verify_decision(
        self,
        topic: str,
        context: str,
        categories: list[str] | None = None,
        existing_files: list[str] | None = None,
        approaches: list[tuple[str, str]] | None = None,
    ) -> SelfConsistencyVerdict:
        """Run self-consistency check on a high-stakes decision.

        Args:
            topic: Short description of the decision (e.g., "Add connection pool")
            context: Why this decision is being considered now
            categories: Tags to select appropriate generators (e.g., ["async", "database"])
            existing_files: Files that will be modified — used for fit-to-project scoring
            approaches: Override auto-generation with explicit (title, description) list.
                       If None, auto-generates 3 approaches.

        Returns:
            SelfConsistencyVerdict with scored approaches and confidence rating
        """
        # Generate candidate approaches
        if approaches is None:
            approaches = self._generate_approaches(topic, context, categories or [])

        # Ensure exactly 3 approaches
        while len(approaches) < 3:
            approaches.append((f"Alternative {len(approaches)+1}", "Additional candidate approach"))
        approaches = approaches[:3]

        # Score each approach
        scored = []
        for i, (title, description) in enumerate(approaches):
            scored_approach = self._score_approach(
                approach_id=f"approach-{i+1}",
                title=title,
                description=description,
                topic=topic,
                context=context,
                existing_files=existing_files or [],
            )
            scored.append(scored_approach)

        # Determine consensus and confidence
        scores = [s.overall_score for s in scored]
        winner = max(scored, key=lambda s: s.overall_score)
        consensus_strength = self._compute_consensus(scores)
        confidence = self._compute_confidence(scores, winner, consensus_strength)

        # Generate concerns for low-confidence verdicts
        concerns = []
        if confidence < 0.80:
            concerns.append(
                f"Confidence {confidence:.0%} is below 80% threshold — "
                "surface this decision to Bashara before proceeding."
            )
        if winner.risk > 0.5:
            concerns.append(f"Winner approach has HIGH risk score ({winner.risk:.0%}) — evaluate carefully.")
        if consensus_strength < 0.3:
            concerns.append(
                f"Low consensus ({consensus_strength:.0%}) — approaches strongly disagree. "
                "This suggests the decision space is not well-understood."
            )
        if any(s.violations for s in scored):
            violators = [s for s in scored if s.violations]
            concerns.append(
                f"{len(violators)}/3 approaches have architecture violations — "
                "check swarm-bot conventions before proceeding."
            )

        # Build recommendation
        recommendation = self._build_recommendation(winner, confidence, consensus_strength)

        return SelfConsistencyVerdict(
            decision_topic=topic,
            approaches=scored,
            winner=winner,
            confidence=confidence,
            consensus_strength=consensus_strength,
            should_proceed=confidence >= 0.80,
            concerns=concerns,
            recommendation=recommendation,
        )

    def _generate_approaches(
        self, topic: str, context: str, categories: list[str]
    ) -> list[tuple[str, str]]:
        """Generate 3 diverse approaches based on topic and categories."""
        # Check registered generators
        for cat in categories:
            if cat in _APPROACH_GENERATORS:
                result = _APPROACH_GENERATORS[cat](topic, context)
                if result:
                    return result

        # Check topic keywords
        topic_lower = topic.lower()
        if any(k in topic_lower for k in ["database", "sqlite", "aiosqlite", "db"]) and "async" in _APPROACH_GENERATORS:
            return _APPROACH_GENERATORS["async"](topic, context)

        return _default_3_approaches(topic, context)

    def _score_approach(
        self,
        approach_id: str,
        title: str,
        description: str,
        topic: str,
        context: str,
        existing_files: list[str],
    ) -> ScoredApproach:
        """Score a single approach across 4 dimensions using heuristic analysis."""
        reasoning: list[str] = []
        violations: list[str] = []

        # ---- Correctness (0.0–1.0) ----
        # Does the approach actually solve the stated problem?
        correctness, r = self._score_correctness(title, description, topic, context)
        reasoning.extend(r)

        # ---- Maintainability (0.0–1.0) ----
        # Will future maintainers understand it? Is it consistent with swarm-bot patterns?
        maintainability, m_r, m_v = self._score_maintainability(
            title, description, existing_files
        )
        reasoning.extend(m_r)
        violations.extend(m_v)

        # ---- Risk (0.0–1.0) ----
        # What's the probability of production issues?
        risk, ri_r = self._score_risk(title, description, context)
        reasoning.extend(ri_r)

        # ---- Fit to project (0.0–1.0) ----
        # Does it match swarm-bot's async/aiogram/litellm architecture?
        fit, f_r, f_v = self._score_fit(title, description)
        reasoning.extend(f_r)
        violations.extend(f_v)

        return ScoredApproach(
            approach_id=approach_id,
            title=title,
            description=description,
            correctness=correctness,
            maintainability=maintainability,
            risk=risk,
            fit_to_project=fit,
            reasoning=reasoning,
            violations=violations,
        )

    def _score_correctness(
        self, title: str, description: str, topic: str, context: str
    ) -> tuple[float, list[str]]:
        """Score whether the approach actually solves the problem."""
        reasoning = []
        score = 0.7  # baseline

        combined = f"{title} {description}".lower()
        topic_lower = topic.lower()

        # Correctness boosters
        if any(k in combined for k in ["reuses", "existing", "compatible", "layer"]):
            score += 0.05
            reasoning.append("Uses existing infrastructure — correctness boosted")
        if "aiosqlite" in combined or "async" in combined:
            if "async" in topic_lower or "concurrent" in context.lower():
                score += 0.1
                reasoning.append("Async approach matches concurrent context requirement")
        if any(k in combined for k in ["thorough", "test", "validate", "verify"]):
            score += 0.05
            reasoning.append("Includes validation — correctness boosted")

        # Correctness penalties
        if any(k in combined for k in ["drop", "replace all", "rip out", "full rewrite"]) and ("full rewrite" in combined or "replace all" in combined):
            score -= 0.15
            reasoning.append("Full replacement is high-risk for correctness")
        if "quick" in combined or "hack" in combined or "workaround" in combined:
            score -= 0.1
            reasoning.append("Quick fix signals correctness risk")

        return max(0.1, min(1.0, score)), reasoning

    def _score_maintainability(
        self, title: str, description: str, existing_files: list[str]
    ) -> tuple[float, list[str], list[str]]:
        """Score whether future maintainers will understand it."""
        reasoning = []
        violations = []
        score = 0.7

        combined = f"{title} {description}".lower()

        # Maintainability boosters
        if any(k in combined for k in ["thin", "minimal", "adapter", "wrapper"]):
            score += 0.1
            reasoning.append("Thin abstraction — easy to understand and remove")
        if any(k in combined for k in ["consistent", "same pattern", "follows existing"]):
            score += 0.1
            reasoning.append("Follows existing code patterns")
        if any(k in combined for k in ["document", "explain", "clear"]):
            score += 0.05
            reasoning.append("Explicit documentation signal")

        # Maintainability penalties
        if len(existing_files) > 5 and any(k in combined for k in ["drop", "replace all"]):
            score -= 0.15
            violations.append("Aggressive refactor across many files hurts maintainability")
        if any(k in combined for k in ["magic", "implicit", "surprising", "clever"]):
            score -= 0.1
            violations.append("'Clever' code is hard to maintain")

        return max(0.1, min(1.0, score)), reasoning, violations

    def _score_risk(
        self, title: str, description: str, context: str
    ) -> tuple[float, list[str]]:
        """Score probability of production issues."""
        reasoning = []
        score = 0.3  # baseline: higher risk = higher number

        combined = f"{title} {description} {context}".lower()

        # Risk reducers
        if any(k in combined for k in ["thin", "layer", "adapter", "wrapper", "compatible"]):
            score -= 0.15
            reasoning.append("Thin layer reduces blast radius")
        if any(k in combined for k in ["test", "validate", "verify", "check"]):
            score -= 0.1
            reasoning.append("Testing discipline reduces risk")
        if any(k in combined for k in ["canary", "gradual", "feature flag", "gradual roll"]):
            score -= 0.1
            reasoning.append("Gradual rollout reduces risk")

        # Risk amplifiers
        if any(k in combined for k in ["drop", "replace all", "rip out", "full rewrite"]):
            score += 0.25
            reasoning.append("Full replacement is high blast radius")
        if any(k in combined for k in ["global", "singleton", "shared state"]):
            score += 0.1
            reasoning.append("Shared state increases failure modes")
        if "database" in combined or "migration" in combined:
            score += 0.1
            reasoning.append("Database changes carry production risk")

        return max(0.0, min(1.0, score)), reasoning

    def _score_fit(
        self, title: str, description: str
    ) -> tuple[float, list[str], list[str]]:
        """Score alignment with swarm-bot's async/aiogram/litellm architecture."""
        reasoning = []
        violations = []
        score = 0.7

        combined = f"{title} {description}".lower()

        # Fit boosters
        if any(k in combined for k in ["aiosqlite", "asyncio", "async", "await"]):
            score += 0.15
            reasoning.append("Matches async architecture")
        if any(k in combined for k in ["aiogram", "handler", "router", "telegram"]):
            score += 0.1
            reasoning.append("Uses aiogram patterns")
        if any(k in combined for k in ["litellm", "fallback", "model", "provider"]):
            score += 0.1
            reasoning.append("Compatible with litellm routing")
        if any(k in combined for k in ["pydantic", "dataclass", "type hint"]):
            score += 0.05
            reasoning.append("Uses type-safe patterns preferred in codebase")

        # Fit penalties
        if any(k in combined for k in ["threading", "thread", "blocking", "sync"]):
            score -= 0.2
            violations.append("Uses sync/blocking patterns — anti-pattern in async codebase")
        if any(k in combined for k in ["global", "singleton"]):
            score -= 0.05
            violations.append("Global state conflicts with testability goals")
        if "sqlite" in combined and "aiosqlite" not in combined:
            score -= 0.15
            violations.append("Sync sqlite used — aiosqlite is the project standard")

        return max(0.1, min(1.0, score)), reasoning, violations

    def _compute_consensus(self, scores: list[float]) -> float:
        """Compute how much approaches agree (0.0 = total disagreement, 1.0 = perfect agreement)."""
        if len(scores) < 2:
            return 1.0
        # Standard deviation of scores — low std = high consensus
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = variance ** 0.5
        # Map std to consensus: std 0.0 → 1.0, std 0.5 → 0.0
        consensus = max(0.0, 1.0 - (std * 2))
        return consensus

    def _compute_confidence(
        self, scores: list[float], winner, consensus: float
    ) -> float:
        """Compute confidence in the winning approach."""
        # Confidence = winner_score * consensus * stability
        winner_score = winner.overall_score
        # Stability: how much better is winner vs others?
        if len(scores) >= 2:
            sorted_scores = sorted(scores, reverse=True)
            margin = sorted_scores[0] - sorted_scores[1]
            stability = min(1.0, margin / 0.3)  # 0.3 margin = full stability
        else:
            stability = 1.0

        confidence = winner_score * consensus * (0.5 + 0.5 * stability)
        return max(0.0, min(1.0, confidence))

    def _build_recommendation(
        self, winner: ScoredApproach, confidence: float, consensus: float
    ) -> str:
        """Build human-readable one-line recommendation."""
        if confidence >= 0.80 and consensus >= 0.60:
            return (
                f"✅ Proceed with '{winner.title}' "
                f"(confidence {confidence:.0%}, consensus {consensus:.0%})"
            )
        elif confidence >= 0.60:
            return (
                f"⚠️ Proceed with caution — '{winner.title}' "
                f"wins but confidence {confidence:.0%} < 80%. Review concerns first."
            )
        else:
            return (
                f"🚫 Do not proceed — confidence {confidence:.0%} too low. "
                "Surface to user or revisit decision framing."
            )

    # ---------------------------------------------------------------------------
    # Convenience methods
    # ---------------------------------------------------------------------------

    async def quick_check(
        self, topic: str, context: str
    ) -> SelfConsistencyVerdict:
        """Run a fast self-consistency check with default 3-approaches.

        Use this for medium-stakes decisions where formal verification is overkill.
        """
        return await self.verify_decision(topic=topic, context=context)

    def format_verdict(self, verdict: SelfConsistencyVerdict) -> str:
        """Format verdict as human-readable string for Telegram display."""
        lines = [
            f"🔍 Self-Consistency Check: {verdict.decision_topic}",
            "",
        ]

        for app in sorted(verdict.approaches, key=lambda a: a.overall_score, reverse=True):
            badge = "🏆" if app.recommended else "  "
            lines.append(
                f"{badge} [{app.overall_score:.2f}] {app.title} "
                f"(C:{app.correctness:.0%} M:{app.maintainability:.0%} "
                f"R:{app.risk:.0%} F:{app.fit_to_project:.0%})"
            )
            if app.violations:
                for v in app.violations:
                    lines.append(f"    ⚠️ {v}")

        lines.append("")
        lines.append(f"Confidence: {verdict.confidence:.0%} | Consensus: {verdict.consensus_strength:.0%}")
        lines.append(f"Recommendation: {verdict.recommendation}")

        if verdict.concerns:
            lines.append("")
            lines.append("⚠️ Concerns:")
            for c in verdict.concerns:
                lines.append(f"  • {c}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience singleton
# ---------------------------------------------------------------------------

_verifier: SelfConsistencyVerifier | None = None


def get_self_consistency_verifier(
    project_root: str | None = None,
) -> SelfConsistencyVerifier:
    """Return global SelfConsistencyVerifier singleton."""
    global _verifier
    if _verifier is None:
        _verifier = SelfConsistencyVerifier(project_root)
    return _verifier
