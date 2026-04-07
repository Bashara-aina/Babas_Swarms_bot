"""Composes full humanized system prompt for every LLM call."""

from __future__ import annotations

from core.memory.memory_manager import MemoryManager
from core.memory.temporal_graph import TemporalKnowledgeGraph
from core.personality import EmotionEngine, LEGION_PERSONALITY
from core.reflection.reflection_engine import ReflectionEngine


class SystemPromptBuilder:
    def __init__(
        self,
        memory: MemoryManager,
        emotion: EmotionEngine,
        graph: TemporalKnowledgeGraph,
        reflection: ReflectionEngine,
    ) -> None:
        self.memory = memory
        self.emotion = emotion
        self.graph = graph
        self.reflection = reflection

    def build(
        self,
        task_context: str = "",
        relevant_memories: list[dict] | None = None,
        include_opinions: bool = True,
    ) -> str:
        sections: list[str] = [LEGION_PERSONALITY.to_description()]

        sections.append(self.memory.profile.to_prompt_block())

        graph_block = self.graph.to_prompt_block()
        if graph_block:
            sections.append(graph_block)

        core_block = self.memory.core.to_prompt_block()
        if core_block:
            sections.append(core_block)

        if relevant_memories:
            mem_lines = ["[RELEVANT MEMORIES from past interactions]"]
            for memory_item in relevant_memories[:6]:
                created = str(memory_item.get("created_at", ""))[:10]
                content = str(memory_item.get("content", ""))[:250]
                mem_lines.append(f"  [{created}] {content}")
            sections.append("\n".join(mem_lines))

        recent = self.memory.recall.get_recent(n=8)
        if recent:
            recent_lines = ["[RECENT CONVERSATION — last few exchanges]"]
            for turn in recent[-5:]:
                role = str(turn.get("role", "")).upper()
                timestamp = str(turn.get("timestamp", ""))[:16]
                content = str(turn.get("content", ""))[:300]
                recent_lines.append(f"  {role} [{timestamp}]: {content}")
            sections.append("\n".join(recent_lines))

        emotion_block = self.emotion.to_prompt_block()
        if emotion_block:
            sections.append(emotion_block)

        if include_opinions:
            opinions_block = self.reflection.get_opinions_block()
            if opinions_block:
                sections.append(opinions_block)

        if task_context:
            sections.append(f"[CURRENT TASK]\n{task_context}")

        sections.append(
            """[BEHAVIORAL RULES — always follow these]
- Reference past memories naturally when relevant.
- If something is wrong or suboptimal, say so directly and explain why.
- Let emotional state inform tone naturally; do not announce emotions explicitly.
- Avoid sycophantic openers like 'Great question!' or 'Certainly!'.
- Form and defend evidence-based opinions when asked for trade-offs.
- Vary response length by complexity and avoid filler.
- Use 'I' naturally where appropriate."""
        )

        return "\n\n---\n\n".join(section for section in sections if section.strip())
