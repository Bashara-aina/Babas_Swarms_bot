#!/usr/bin/env python3
"""
LiteLLM callback that strips verbose tool descriptions from API requests.
Saves ~60K tokens per request from the context floor.
"""
from __future__ import annotations

from typing import Any

from litellm.integrations.custom_logger import CustomLogger


class ToolSchemaStripperCallback(CustomLogger):
    """Strip tool/param descriptions from API requests to save ~60K tokens."""

    async def async_pre_call_hook(
        self,
        user_api_key_dict: Any,
        cache: Any,
        data: dict,
        call_type: Any,
    ) -> dict | None:
        """Remove verbose descriptions from tool schemas before forwarding."""
        tools = data.get("tools")
        if not isinstance(tools, list):
            return None

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
