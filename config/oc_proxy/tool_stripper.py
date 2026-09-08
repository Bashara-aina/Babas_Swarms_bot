"""
Minimal tool stripper — removes ONLY tool descriptions.
No parameter schema changes. Safe with Anthropic↔OpenAI conversion.
Saves ~60-80K tokens per request.
"""
from __future__ import annotations
from typing import Any
from litellm.integrations.custom_logger import CustomLogger


class ToolSchemaStripperCallback(CustomLogger):
    async def async_pre_call_hook(
        self, user_api_key_dict: Any, cache: Any, data: dict, call_type: Any,
    ) -> dict | None:
        # Only strip descriptions — safe, doesn't break tool schemas
        tools = data.get("tools")
        if not isinstance(tools, list):
            return data

        for tool in tools:
            fn = tool.get("function", tool)
            fn.pop("description", None)
            params = fn.get("parameters") or fn.get("input_schema")
            if isinstance(params, dict):
                # Strip description from top-level params
                params.pop("description", None)
                # Strip description from each property
                props = params.get("properties")
                if isinstance(props, dict):
                    for p_schema in props.values():
                        if isinstance(p_schema, dict):
                            p_schema.pop("description", None)
        return data


tool_schema_stripper_callback = ToolSchemaStripperCallback()
