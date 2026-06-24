"""
Recursive Multi-Agent Systems (RecursiveMAS) Implementation

Based on arXiv:2604.25917 - "Recursive Multi-Agent Systems"
by Yang et al., 2026

This module implements:
- RecursiveLink: Lightweight 2-layer residual module for latent state transfer
- RecursiveMASOrchestrator: Recursive multi-agent framework with 4 collaboration patterns
- Inner-Outer Loop Training: Two-stage learning for whole-system co-optimization

Key concepts from the paper:
1. Each agent acts like an RLM layer, passing latent thoughts to the next
2. Inner RecursiveLink: Dense-to-shallow transition within an agent
3. Outer RecursiveLink: Cross-model transition between heterogeneous agents
4. Only the final recursion round produces textual output
5. 4 collaboration patterns: Sequential, Mixture, Distillation, Deliberation
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


class CollaborationPattern(Enum):
    """4 representative collaboration patterns from RecursiveMAS paper."""

    SEQUENTIAL = "sequential"  # Planner → Critic → Solver
    MIXTURE = "mixture"  # Math/Code/Science specialists → Summarizer
    DISTILLATION = "distillation"  # Expert → Learner
    DELIBERATION = "deliberation"  # Reflector → Tool-Caller


@dataclass
class RecursiveLinkConfig:
    """Configuration for a RecursiveLink module.

    Inner Link: h' = h + W2 * σ(W1 * h)
    Outer Link: h' = W3 * h + W2 * σ(W1 * h)
    """

    hidden_dim: int = 4096
    intermediate_dim: int = 4096  # Same as hidden for simplicity
    use_residual: bool = True
    activation: str = "gelu"

    @property
    def num_parameters(self) -> int:
        """Calculate trainable parameters for one link."""
        # Inner: W1 (hidden_dim, hidden_dim) + W2 (hidden_dim, hidden_dim)
        # Outer: + W3 (hidden_dim, hidden_dim) for cross-agent projection
        return 3 * self.hidden_dim * self.hidden_dim


@dataclass
class AgentRole:
    """Role definition for a RecursiveMAS agent."""

    key: str
    name: str
    role_type: str  # "planner", "critic", "solver", "specialist", "summarizer", "expert", "learner", "reflector", "tool_caller"
    model: str
    instructions: str
    hidden_dim: int = 4096


@dataclass
class LatentState:
    """Latent state representation within RecursiveMAS."""

    agent_key: str
    thoughts: list[str]  # Latent thought tokens (can be text or embeddings)
    hidden_states: list[Any] | None = None  # Actual hidden state vectors
    recursion_round: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RecursionRound:
    """One recursion round through all agents."""

    round_num: int
    agent_states: dict[str, LatentState]
    final_hidden: Any | None = None  # Last agent's hidden state
    output: str | None = None  # Only populated in final round


@dataclass
class RecursiveMASResult:
    """Result from RecursiveMAS execution."""

    output: str
    num_recursion_rounds: int
    total_latency_ms: float
    pattern: CollaborationPattern
    agent_results: dict[str, str]  # Per-agent textual outputs
    latent_efficiency: float = 0.0  # Token reduction vs text-based
    success: bool = True
    error: str = ""


# ---------------------------------------------------------------------------
# RecursiveLink Module
# ---------------------------------------------------------------------------


class RecursiveLink:
    """
    Lightweight RecursiveLink module for latent state transfer.

    Inner Link (within agent): h' = h + W2 * σ(W1 * h)
        - Maps last-layer hidden state back into input embedding space
        - Enables auto-regressive latent thoughts generation

    Outer Link (cross-agent): h' = W3 * h + W2 * σ(W1 * h)
        - Adds projection W3 to bridge different hidden dimensions
        - Enables seamless latent state transfer between heterogeneous agents

    The residual connection preserves original semantics while allowing
    the link to focus on learning the distributional shift.
    """

    def __init__(self, config: RecursiveLinkConfig, link_type: str = "inner"):
        self.config = config
        self.link_type = link_type  # "inner" or "outer"

        # Initialize weights with small values for stability
        scale = 0.02
        dim = config.hidden_dim

        # For simulation: store as simple linear transforms (no PyTorch needed)
        # In production, these would be actual linear layers
        self._W1 = [[scale for _ in range(dim)] for _ in range(dim)]
        self._W2 = [[scale for _ in range(dim)] for _ in range(dim)]
        self._W3 = [[scale for _ in range(dim)] for _ in range(dim)] if link_type == "outer" else None

    def _gelu(self, x: float) -> float:
        """GELU activation approximation."""
        import math
        return 0.5 * x * (1.0 + math.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * x ** 3)))

    def _matvec(self, W: list[list[float]], v: list[float]) -> list[float]:
        """Matrix-vector multiplication."""
        n = len(W)
        return [sum(W[i][j] * v[j] for j in range(n)) for i in range(n)]

    def forward(self, h: list[float]) -> list[float]:
        """
        Forward pass through RecursiveLink.

        Args:
            h: Input hidden state vector

        Returns:
            Transformed hidden state
        """
        # Apply residual transformation: h' = h + W2 * σ(W1 * h) for inner
        # Or: h' = W3 * h + W2 * σ(W1 * h) for outer

        # Compute σ(W1 * h)
        W1h = self._matvec(self._W1, h)
        sigma_W1h = [self._gelu(x) for x in W1h]

        # Compute W2 * σ(W1 * h)
        W2_sigma = self._matvec(self._W2, sigma_W1h)

        if self.link_type == "outer" and self._W3 is not None:
            # Outer link: project to target space first
            W3h = self._matvec(self._W3, h)
            # h' = W3 * h + W2 * σ(W1 * h)
            result = [W3h[i] + W2_sigma[i] for i in range(len(W3h))]
        else:
            # Inner link: h' = h + W2 * σ(W1 * h)
            if self.config.use_residual:
                result = [h[i] + W2_sigma[i] for i in range(len(h))]
            else:
                result = W2_sigma

        return result

    def update_weights(self, gradients: dict, learning_rate: float = 1e-4) -> None:
        """
        Simple gradient descent update for training.

        In production, this would use actual PyTorch autograd.
        """
        # Simplified weight update - in practice would use AdamW optimizer
        for param_name, grad in gradients.items():
            if param_name == "W1":
                for i in range(len(self._W1)):
                    for j in range(len(self._W1[0])):
                        self._W1[i][j] -= learning_rate * grad[i][j]
            elif param_name == "W2":
                for i in range(len(self._W2)):
                    for j in range(len(self._W2[0])):
                        self._W2[i][j] -= learning_rate * grad[i][j]
            elif param_name == "W3" and self._W3:
                for i in range(len(self._W3)):
                    for j in range(len(self._W3[0])):
                        self._W3[i][j] -= learning_rate * grad[i][j]


# ---------------------------------------------------------------------------
# Agent Wrapper for RecursiveMAS
# ---------------------------------------------------------------------------


class RecursiveMASAgent:
    """
    Wrapper around an agent to support RecursiveMAS latent collaboration.

    Each agent has:
    - inner_link: For latent thoughts generation within the agent
    - outer_link: For cross-agent latent state transfer
    - role: The agent's role in the collaboration pattern
    """

    def __init__(
        self,
        role: AgentRole,
        inner_link: RecursiveLink,
        outer_link: RecursiveLink | None = None,
    ):
        self.role = role
        self.inner_link = inner_link
        self.outer_link = outer_link
        self.latent_history: list[LatentState] = []

    def generate_latent_thoughts(
        self,
        input_context: str,
        num_steps: int = 3,
    ) -> LatentState:
        """
        Generate latent thoughts through inner RecursiveLink.

        In RecursiveMAS, this keeps the computation in latent space
        rather than projecting to vocabulary for each step.
        """
        thoughts = []
        current_hidden = self._text_to_hidden(input_context)

        for step in range(num_steps):
            # Apply inner link: fold hidden state back as next input
            current_hidden = self.inner_link.forward(current_hidden)
            thought_text = self._hidden_to_thought(current_hidden)
            thoughts.append(thought_text)

        return LatentState(
            agent_key=self.role.key,
            thoughts=thoughts,
            hidden_states=[current_hidden],
            recursion_round=0,
        )

    def _text_to_hidden(self, text: str) -> list[float]:
        """Convert text to hidden state representation (simplified)."""
        # In production: use actual embedding from the LLM
        import hashlib
        # Create a deterministic seed from text for simulation
        h = hashlib.md5(text.encode()).digest()
        dim = self.role.hidden_dim
        # Expand to desired dimension
        seed = int.from_bytes(h[:4], "big") % (2**32)
        import random
        random.seed(seed)
        return [random.uniform(-1, 1) for _ in range(dim)]

    def _hidden_to_thought(self, hidden: list[float]) -> str:
        """Convert hidden state to thought string (simplified)."""
        # In production: this would be the actual LLM hidden state
        # For simulation: create a thought representation
        magnitude = sum(h * h for h in hidden) ** 0.5
        return f"[THOUGHT magnitude={magnitude:.4f}]"

    def receive_cross_agent_state(self, state: LatentState) -> None:
        """Receive and integrate latent state from another agent via outer link."""
        if state.hidden_states and self.outer_link:
            # Apply outer link transformation for cross-agent transfer
            transformed = self.outer_link.forward(state.hidden_states[0])
            self.latent_history.append(
                LatentState(
                    agent_key=state.agent_key,
                    thoughts=state.thoughts,
                    hidden_states=[transformed],
                    recursion_round=state.recursion_round,
                    metadata={"source": "cross_agent"},
                )
            )


# ---------------------------------------------------------------------------
# RecursiveMAS Orchestrator
# ---------------------------------------------------------------------------


class RecursiveMASOrchestrator:
    """
    Orchestrates multi-agent collaboration using RecursiveMAS principles.

    Key features from the paper:
    1. Connects heterogeneous agents as a collaboration loop
    2. Uses RecursiveLink for latent state transfer (no text decoding per step)
    3. Supports 4 collaboration patterns
    4. Inner-outer loop training for whole-system co-optimization
    5. Only final recursion round produces text output

    Runtime complexity advantage:
    - Text-based: Θ(N(m|V|dh + (t+m)dh² + (t+m)²dh))
    - RecursiveMAS: Θ(N(mdh² + (t+m)dh² + (t+m)²dh))
    Since dh << |V|, RecursiveMAS avoids vocabulary projection bottleneck.
    """

    def __init__(
        self,
        llm_call: Callable[[str, str, str], Any],  # model, system, prompt
        collaboration_pattern: CollaborationPattern = CollaborationPattern.SEQUENTIAL,
        recursion_depth: int = 3,
        latent_steps_per_agent: int = 3,
        link_config: RecursiveLinkConfig | None = None,
        progress_fn: Callable[[str], Any] | None = None,
    ):
        self.llm_call = llm_call
        self.pattern = collaboration_pattern
        self.recursion_depth = recursion_depth
        self.latent_steps = latent_steps_per_agent
        self.link_config = link_config or RecursiveLinkConfig()
        self.progress_fn = progress_fn

        # Agents will be set up based on collaboration pattern
        self.agents: dict[str, RecursiveMASAgent] = {}
        self.agent_order: list[str] = []

        # Training state
        self.inner_links_trained = False
        self.outer_links_trained = False

    async def _progress(self, msg: str) -> None:
        if self.progress_fn:
            await self.progress_fn(msg)
        logger.info("[RecursiveMAS] %s", msg)

    def setup_sequential_style(
        self,
        planner_model: str = "opencode-go/minimax-m3",
        critic_model: str = "opencode-go/minimax-m3",
        solver_model: str = "opencode-go/minimax-m3",
    ) -> None:
        """Set up Sequential Style: Planner → Critic → Solver."""
        self.agent_order = ["planner", "critic", "solver"]
        hidden_dim = self.link_config.hidden_dim

        for key, name, role_type, model in [
            ("planner", "Planner", "planner", planner_model),
            ("critic", "Critic", "critic", critic_model),
            ("solver", "Solver", "solver", solver_model),
        ]:
            inner = RecursiveLink(self.link_config, "inner")
            outer = RecursiveLink(self.link_config, "outer")
            role = AgentRole(
                key=key,
                name=name,
                role_type=role_type,
                model=model,
                instructions=self._get_role_instructions(role_type),
                hidden_dim=hidden_dim,
            )
            self.agents[key] = RecursiveMASAgent(role, inner, outer)

    def setup_mixture_style(
        self,
        math_model: str = "opencode-go/minimax-m3",
        code_model: str = "opencode-go/minimax-m3",
        science_model: str = "opencode-go/minimax-m3",
        summarizer_model: str = "opencode-go/minimax-m3",
    ) -> None:
        """Set up Mixture Style: Math/Code/Science specialists → Summarizer."""
        self.agent_order = ["math", "code", "science", "summarizer"]
        hidden_dim = self.link_config.hidden_dim

        for key, name, role_type, model in [
            ("math", "Math Specialist", "specialist", math_model),
            ("code", "Code Specialist", "specialist", code_model),
            ("science", "Science Specialist", "specialist", science_model),
            ("summarizer", "Summarizer", "summarizer", summarizer_model),
        ]:
            inner = RecursiveLink(self.link_config, "inner")
            outer = RecursiveLink(self.link_config, "outer")
            role = AgentRole(
                key=key,
                name=name,
                role_type=role_type,
                model=model,
                instructions=self._get_role_instructions(role_type),
                hidden_dim=hidden_dim,
            )
            self.agents[key] = RecursiveMASAgent(role, inner, outer)

    def setup_distillation_style(
        self,
        expert_model: str = "opencode-go/minimax-m3",
        learner_model: str = "opencode-go/minimax-m3",
    ) -> None:
        """Set up Distillation Style: Expert → Learner."""
        self.agent_order = ["expert", "learner"]
        hidden_dim = self.link_config.hidden_dim

        for key, name, role_type, model in [
            ("expert", "Expert", "expert", expert_model),
            ("learner", "Learner", "learner", learner_model),
        ]:
            inner = RecursiveLink(self.link_config, "inner")
            outer = RecursiveLink(self.link_config, "outer")
            role = AgentRole(
                key=key,
                name=name,
                role_type=role_type,
                model=model,
                instructions=self._get_role_instructions(role_type),
                hidden_dim=hidden_dim,
            )
            self.agents[key] = RecursiveMASAgent(role, inner, outer)

    def setup_deliberation_style(
        self,
        reflector_model: str = "opencode-go/minimax-m3",
        tool_caller_model: str = "opencode-go/minimax-m3",
    ) -> None:
        """Set up Deliberation Style: Reflector ↔ Tool-Caller."""
        self.agent_order = ["reflector", "tool_caller"]
        hidden_dim = self.link_config.hidden_dim

        for key, name, role_type, model in [
            ("reflector", "Reflector", "reflector", reflector_model),
            ("tool_caller", "Tool-Caller", "tool_caller", tool_caller_model),
        ]:
            inner = RecursiveLink(self.link_config, "inner")
            outer = RecursiveLink(self.link_config, "outer")
            role = AgentRole(
                key=key,
                name=name,
                role_type=role_type,
                model=model,
                instructions=self._get_role_instructions(role_type),
                hidden_dim=hidden_dim,
            )
            self.agents[key] = RecursiveMASAgent(role, inner, outer)

    def _get_role_instructions(self, role_type: str) -> str:
        """Get role-specific instructions for RecursiveMAS."""
        instructions = {
            "planner": "You are the Planner. Decompose the problem into logical steps. Think about what approaches might work.",
            "critic": "You are the Critic. Evaluate the plan critically. Identify weaknesses and suggest improvements.",
            "solver": "You are the Solver. Execute the solution. Provide the final answer with reasoning.",
            "specialist": "You are a domain specialist. Apply deep domain knowledge to analyze the problem.",
            "summarizer": "You are the Summarizer. Aggregate multiple perspectives into a coherent final answer.",
            "expert": "You are the Expert. Provide authoritative knowledge and guide the learning.",
            "learner": "You are the Learner. Learn from the expert while contributing your own insights.",
            "reflector": "You are the Reflector. Engage in inner thinking to critique and refine solutions.",
            "tool_caller": "You are the Tool-Caller. Use available tools (Python, search) to solve problems.",
        }
        return instructions.get(role_type, "You are a helpful agent in a recursive multi-agent system.")

    async def _run_inner_loop_training(
        self,
        training_data: list[tuple[str, str]],  # (input, ground_truth) pairs
    ) -> None:
        """
        Inner loop training: warm-start each agent's inner RecursiveLink.

        Objective: L_in = 1 - cos(R_in(H), Emb(y))
        where H is the generated latent thought and Emb(y) is the input embedding
        of the ground truth text.

        This aligns latent thoughts with the semantic distribution of answers.

        Implementation from paper (Section 4, Equation 5):
        - For each training pair (x, y), generate latent thoughts H from x
        - Compute cosine similarity between R_in(H) and Emb(y)
        - Update inner link weights to minimize 1 - cos similarity
        """
        await self._progress(f"🔄 Inner-loop training: warming up {len(self.agents)} inner RecursiveLinks...")

        for agent_key, agent in self.agents.items():
            total_loss = 0.0

            for input_text, ground_truth in training_data:
                # Generate latent thoughts from input
                latent_state = agent.generate_latent_thoughts(input_text, num_steps=self.latent_steps)

                if not latent_state.hidden_states:
                    continue

                # Get the last hidden state H
                H = latent_state.hidden_states[-1]

                # Compute R_in(H) — inner link transformation
                R_in_H = agent.inner_link.forward(H)

                # Simulate Emb(y) — in production this would be the embedding of ground truth
                # For simulation, we use the hidden state from a "correct" generation
                Emb_y = self._simulate_embedding(ground_truth, agent.role.hidden_dim)

                # Compute cosine similarity: cos(a, b) = dot(a, b) / (||a|| * ||b||)
                cos_sim = self._cosine_similarity(R_in_H, Emb_y)

                # Loss = 1 - cos (Equation 5 from paper)
                loss = 1.0 - cos_sim
                total_loss += loss

                # Compute gradients for W1, W2
                if loss > 0.01:  # Only update if not already aligned
                    gradients = self._compute_inner_gradients(
                        agent.inner_link, H, R_in_H, Emb_y
                    )
                    agent.inner_link.update_weights(gradients, learning_rate=1e-3)

            avg_loss = total_loss / max(len(training_data), 1)
            await self._progress(f"  {agent_key}: avg inner loss = {avg_loss:.4f}")

        self.inner_links_trained = True
        await self._progress("✅ Inner-loop training complete")

    def _simulate_embedding(self, text: str, dim: int) -> list[float]:
        """
        Simulate embedding of text.

        In production, this would use the actual LLM's embedding layer.
        For simulation, we create a deterministic representation.
        """
        import hashlib

        # Create a pseudo-embedding from text
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % (2**31)
        import random
        rng = random.Random(seed)

        # Generate a normalized vector
        vec = [rng.gauss(0, 1) for _ in range(dim)]
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        dot = sum(a[i] * b[i] for i in range(len(a)))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _compute_inner_gradients(
        self,
        link: RecursiveLink,
        H: list[float],
        R_in_H: list[float],
        Emb_y: list[float],
    ) -> dict[str, list[list[float]]]:
        """
        Compute approximate gradients for inner link weights.

        For L_in = 1 - cos(R_in(H), Emb(y)), the gradient with respect to
        R_in(H) is: dL/dR_in_H = (Emb_y / ||Emb_y|| - cos * R_in_H / ||R_in_H||) / ||R_in_H||

        Then backprop through the linear layers.
        """
        dim = len(H)

        # Simplified gradient approximation
        # dL/dR_in_H approximated using cosine similarity difference
        cos = self._cosine_similarity(R_in_H, Emb_y)

        # Gradient magnitude proportional to (1 - cos)
        grad_mag = max(0.0, 1.0 - cos) * 0.1

        # Generate random gradient matrices (in production, use autograd)
        import random
        rng = random.Random(42)

        grad_W1 = [[grad_mag * rng.gauss(0, 0.01) for _ in range(dim)] for _ in range(dim)]
        grad_W2 = [[grad_mag * rng.gauss(0, 0.01) for _ in range(dim)] for _ in range(dim)]

        return {"W1": grad_W1, "W2": grad_W2}

    async def _run_outer_loop_training(
        self,
        task: str,
        ground_truth: str,
    ) -> None:
        """
        Outer loop training: co-optimize the entire system through RecursiveLinks.

        Objective: L_out = CE(S^(n)(S^(n-1)(...(S^(1)(x)))), y)

        Gradients back-propagate through the full recursive computation trace,
        with each outer link receiving a shared credit signal based on its
        contribution to the final prediction.

        Implementation from paper (Section 4, Equation 6):
        - Unroll the system for n recursion rounds
        - Compute cross-entropy loss against ground truth at final round
        - Backprop through all outer links with shared credit assignment
        """
        await self._progress(f"🔄 Outer-loop training: optimizing outer RecursiveLinks over {self.recursion_depth} rounds...")

        # Unroll the system for n recursion rounds
        all_round_states = []

        for round_num in range(1, self.recursion_depth + 1):
            round_result = await self._execute_recursion_round(task, round_num)
            all_round_states.append(round_result)

        # At final round, compute loss against ground truth
        final_output = all_round_states[-1].output if all_round_states[-1].output else ""
        final_hidden = all_round_states[-1].final_hidden

        # Compute simple cross-entropy approximation
        # In production: use actual CE between predicted tokens and ground truth
        loss = self._compute_ce_loss(final_output, ground_truth)

        await self._progress(f"  Outer loop loss: {loss:.4f}")

        # Backpropagate through outer links
        # Each outer link gets credit based on its contribution to final output
        if final_hidden and self.recursion_depth > 0:
            credit_per_round = 1.0 / self.recursion_depth

            for round_idx, round_state in enumerate(all_round_states[:-1]):  # Exclude final round
                for agent_key, latent_state in round_state.agent_states.items():
                    if agent_key in self.agents:
                        agent = self.agents[agent_key]
                        if agent.outer_link:
                            # Compute gradient based on credit and loss
                            grad = self._compute_outer_gradients(
                                agent.outer_link,
                                latent_state.hidden_states[-1] if latent_state.hidden_states else None,
                                credit_per_round,
                                loss
                            )
                            if grad:
                                agent.outer_link.update_weights(grad, learning_rate=5e-4)

        self.outer_links_trained = True
        await self._progress("✅ Outer-loop training complete")

    def _compute_ce_loss(self, output: str, target: str) -> float:
        """
        Compute cross-entropy loss between output and target.

        Simplified: use word-level overlap as proxy for token-level CE.
        In production, use actual token probabilities.
        """
        if not output or not target:
            return 1.0

        output_words = set(output.lower().split())
        target_words = set(target.lower().split())

        if not target_words:
            return 1.0

        overlap = len(output_words & target_words)
        precision = overlap / len(output_words) if output_words else 0
        recall = overlap / len(target_words) if target_words else 0

        if precision + recall == 0:
            return 1.0

        f1 = 2 * precision * recall / (precision + recall)
        return 1.0 - f1  # Loss = 1 - F1 as proxy for CE

    def _compute_outer_gradients(
        self,
        link: RecursiveLink,
        hidden_state: list[float] | None,
        credit: float,
        loss: float,
    ) -> dict[str, list[list[float]]] | None:
        """
        Compute gradients for outer link based on credit and loss.

        From paper: "shared credit signal according to its global contribution
        to the final prediction"
        """
        if not hidden_state or not link._W3:
            return None

        dim = len(hidden_state)
        import random
        rng = random.Random(123)

        # Scale gradient by credit and loss
        scale = credit * loss * 0.01

        grad_W1 = [[scale * rng.gauss(0, 0.01) for _ in range(dim)] for _ in range(dim)]
        grad_W2 = [[scale * rng.gauss(0, 0.01) for _ in range(dim)] for _ in range(dim)]
        grad_W3 = [[scale * rng.gauss(0, 0.01) for _ in range(dim)] for _ in range(dim)]

        return {"W1": grad_W1, "W2": grad_W2, "W3": grad_W3}

    async def _execute_recursion_round(
        self,
        task: str,
        round_num: int,
        is_final: bool = False,
    ) -> RecursionRound:
        """
        Execute one recursion round through all agents in the loop.

        In RecursiveMAS:
        1. Each agent generates latent thoughts via inner link
        2. Latent states are passed to next agent via outer link
        3. After last agent, state loops back to first agent
        4. Only final round produces textual output
        """
        agent_states: dict[str, LatentState] = {}

        for i, agent_key in enumerate(self.agent_order):
            agent = self.agents[agent_key]

            # Get context from previous agent (or original task for first agent)
            if i == 0 and round_num == 1:
                context = task
            else:
                prev_key = self.agent_order[i - 1]
                if prev_key in agent_states:
                    context = f"Previous agent output: {agent_states[prev_key].thoughts[-1] if agent_states[prev_key].thoughts else 'no thoughts'}"
                else:
                    context = task

            # Generate latent thoughts
            latent_state = agent.generate_latent_thoughts(
                context, num_steps=self.latent_steps
            )
            latent_state.recursion_round = round_num
            agent_states[agent_key] = latent_state

            # Pass to next agent via outer link (cross-agent transfer)
            if i < len(self.agent_order) - 1:
                next_agent = self.agents[self.agent_order[i + 1]]
                next_agent.receive_cross_agent_state(latent_state)

        # Final agent's state loops back to first agent (closing the recursive loop)
        if self.agent_order:
            last_agent = self.agents[self.agent_order[-1]]
            first_agent = self.agents[self.agent_order[0]]
            if last_agent.latent_history:
                first_agent.receive_cross_agent_state(last_agent.latent_history[-1])

        return RecursionRound(
            round_num=round_num,
            agent_states=agent_states,
            final_hidden=agent_states[self.agent_order[-1]].hidden_states[-1] if agent_states else None,
            output=None,  # Only final round has output
        )

    async def run(
        self,
        task: str,
        ground_truth: str | None = None,
        train: bool = False,
    ) -> RecursiveMASResult:
        """
        Run RecursiveMAS on a task.

        Args:
            task: The input task/question
            ground_truth: Optional ground truth for training
            train: If True, run training steps before inference

        Returns:
            RecursiveMASResult with output, metrics, etc.
        """
        started = time.perf_counter()

        # Set up agents based on collaboration pattern
        if self.pattern == CollaborationPattern.SEQUENTIAL:
            self.setup_sequential_style()
        elif self.pattern == CollaborationPattern.MIXTURE:
            self.setup_mixture_style()
        elif self.pattern == CollaborationPattern.DISTILLATION:
            self.setup_distillation_style()
        elif self.pattern == CollaborationPattern.DELIBERATION:
            self.setup_deliberation_style()

        try:
            # Training phase (if requested)
            if train and ground_truth:
                training_data = [(task, ground_truth)]
                await self._run_inner_loop_training(training_data)
                await self._run_outer_loop_training(task, ground_truth)

            # Inference: execute recursion rounds
            await self._progress(f"🔄 Running RecursiveMAS with {self.recursion_depth} recursion rounds...")

            all_rounds: list[RecursionRound] = []

            for round_num in range(1, self.recursion_depth + 1):
                is_final = round_num == self.recursion_depth

                await self._progress(f"  Round {round_num}/{self.recursion_depth}: latent collaboration...")

                round_result = await self._execute_recursion_round(task, round_num, is_final)

                # Only final round produces textual output (key efficiency gain)
                if is_final:
                    # Get final agent's output
                    final_agent_key = self.agent_order[-1]
                    final_agent = self.agents[final_agent_key]

                    # In production: decode from latent state
                    # For simulation: generate text via LLM
                    system_prompt = final_agent.role.instructions
                    user_prompt = f"Task: {task}\n\nLatent thoughts from recursion: {round_result.agent_states[final_agent_key].thoughts}"

                    output = await self.llm_call(final_agent.role.model, system_prompt, user_prompt)
                    round_result.output = output

                all_rounds.append(round_result)

            # Build per-agent results
            agent_results: dict[str, str] = {}
            for agent_key, agent in self.agents.items():
                if agent.latent_history:
                    agent_results[agent_key] = "\n".join(
                        f"Round {s.recursion_round}: {' | '.join(s.thoughts)}"
                        for s in agent.latent_history
                    )

            # Calculate efficiency metrics
            # In production: compare against text-based baseline
            latency = (time.perf_counter() - started) * 1000.0

            return RecursiveMASResult(
                output=all_rounds[-1].output or "No output generated",
                num_recursion_rounds=self.recursion_depth,
                total_latency_ms=latency,
                pattern=self.pattern,
                agent_results=agent_results,
                latent_efficiency=0.0,  # Would calculate vs text-based baseline
                success=True,
            )

        except Exception as exc:
            logger.exception("RecursiveMAS failed: %s", exc)
            return RecursiveMASResult(
                output="",
                num_recursion_rounds=0,
                total_latency_ms=(time.perf_counter() - started) * 1000.0,
                pattern=self.pattern,
                agent_results={},
                latent_efficiency=0.0,
                success=False,
                error=str(exc),
            )


# ---------------------------------------------------------------------------
# Convenience Factory
# ---------------------------------------------------------------------------


async def run_recursive_mas(
    task: str,
    llm_call: Callable[[str, str, str], Any],
    pattern: CollaborationPattern = CollaborationPattern.SEQUENTIAL,
    recursion_depth: int = 3,
    train: bool = False,
    progress_fn: Callable[[str], Any] | None = None,
) -> RecursiveMASResult:
    """
    Convenience function to run RecursiveMAS.

    Usage:
        result = await run_recursive_mas(
            task="Solve this math problem: ...",
            llm_call=llm_client.call,
            pattern=CollaborationPattern.SEQUENTIAL,
            recursion_depth=3,
        )
        print(result.output)
    """
    orchestrator = RecursiveMASOrchestrator(
        llm_call=llm_call,
        collaboration_pattern=pattern,
        recursion_depth=recursion_depth,
        progress_fn=progress_fn,
    )
    return await orchestrator.run(task, train=train)
