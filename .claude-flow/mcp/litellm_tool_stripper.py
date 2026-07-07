#!/usr/bin/env python3
"""
LiteLLM callback that strips verbose tool descriptions from API requests.
Saves ~60K tokens per request from the context floor.
"""
from __future__ import annotations

from typing import Any

from litellm.integrations.custom_logger import CustomLogger


class ToolSchemaStripperCallback(CustomLogger):
    """Strip tool/param descriptions from API requests to save ~60K tokens.

    Also sanitizes assistant messages that would trigger DeepSeek's
    "content or tool_calls must be set" error — this happens when
    Anthropic-to-OpenAI conversion produces an assistant message with
    only empty thinking/reasoning content.
    """

    async def _sanitize_messages(self, data: dict) -> None:
        """Ensure no assistant message has empty content + no tool_calls."""
        messages = data.get("messages")
        if not isinstance(messages, list):
            return
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            has_tool_calls = bool(msg.get("tool_calls"))
            if has_tool_calls:
                continue
            # Corner cases DeepSeek rejects: None, "", [], {}, or whitespace-only
            if not content:
                msg["content"] = "."
            elif isinstance(content, str) and not content.strip():
                msg["content"] = "."
            elif isinstance(content, list) and len(content) == 0:
                msg["content"] = "."
            # Anthropic-format content blocks: if every block is non-text
            # (e.g. only thinking blocks from a cancelled mid-thinking response),
            # the OpenAI adapter converts these to content=None + thinking_blocks,
            # which triggers DeepSeek's "content or tool_calls must be set".
            elif isinstance(content, list):
                has_text_block = any(
                    isinstance(b, dict) and b.get("type") == "text" for b in content
                )
                if not has_text_block:
                    content.append({"type": "text", "text": "."})

    async def async_pre_call_hook(
        self,
        user_api_key_dict: Any,
        cache: Any,
        data: dict,
        call_type: Any,
    ) -> dict | None:
        """Remove verbose descriptions from tool schemas before forwarding."""
        # Fix 1: Sanitize empty assistant messages (prevents 400 errors)
        await self._sanitize_messages(data)

        # Fix 2: Strip tool descriptions
        tools = data.get("tools")
        if not isinstance(tools, list):
            return data

        for tool in tools:
            fn = tool.get("function", tool)
            fn.pop("description", None)
            params = fn.get("parameters") or fn.get("input_schema")
            if isinstance(params, dict):
                props = params.get("properties", {})
                if isinstance(props, dict):
                    for p_schema in props.values():
                        if isinstance(p_schema, dict):
                            p_schema.pop("description", None)
                            p_schema.pop("title", None)
        return data


tool_schema_stripper_callback = ToolSchemaStripperCallback()
