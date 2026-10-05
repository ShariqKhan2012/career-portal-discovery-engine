"""LLM interface for Backend A (in-app agent).

Calls OpenRouter's API with a system prompt and tools. The LLM can
call tools (search, fetch, submit) to research companies.

Concept note — why a separate LLM module: the LLM provider is swappable.
If OpenRouter's free tier is insufficient, we can switch to another
provider by changing this one file.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from ..config import Config
from ..logging import get_logger

logger = get_logger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm(
    messages: list[dict[str, str]],
    config: Config,
    tools: list[dict] | None = None,
    temperature: float = 0.1,
) -> dict[str, Any]:
    """Call the LLM via OpenRouter.

    Returns the assistant's response with tool calls if any.
    """
    if not config.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    payload: dict[str, Any] = {
        "model": config.openrouter_model,
        "messages": messages,
        "temperature": temperature,
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        resp = httpx.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {config.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


def call_llm_with_tools(
    messages: list[dict[str, str]],
    tools: list[dict],
    tool_handlers: dict[str, callable],
    config: Config,
    max_iterations: int = 10,
) -> dict[str, Any]:
    """Call the LLM with tool support.

    The LLM can call tools, and we execute them and feed the results back.
    Returns the final response.
    """
    for i in range(max_iterations):
        response = call_llm(messages, config, tools)

        # Check if the LLM wants to call a tool
        tool_calls = response.get("tool_calls", [])
        if not tool_calls:
            return response

        # Execute tool calls
        messages.append(response)
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])

            logger.info(f"LLM calling tool: {function_name}({function_args})")

            handler = tool_handlers.get(function_name)
            if handler:
                result = handler(**function_args)
            else:
                result = f"Unknown tool: {function_name}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": result if isinstance(result, str) else json.dumps(result),
            })

    return response
