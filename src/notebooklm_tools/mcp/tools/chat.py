"""Chat tools - Query and conversation management."""

from typing import Any

from ._utils import get_client, get_query_timeout, logged_tool


@logged_tool()
def notebook_query(
    notebook_id: str,
    query: str,
    source_ids: list[str] | None = None,
    conversation_id: str | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Ask AI about EXISTING sources already in notebook. NOT for finding new sources.

    Use research_start instead for: deep research, web search, find new sources, Drive search.

    Args:
        notebook_id: Notebook UUID
        query: Question to ask
        source_ids: Source IDs to query (default: all)
        conversation_id: For follow-up questions
        timeout: Request timeout in seconds (default: from env NOTEBOOKLM_QUERY_TIMEOUT or 120.0)
    """
    try:
        client = get_client()
        timeout = timeout or get_query_timeout()

        result = client.query(
            notebook_id=notebook_id,
            query_text=query,
            source_ids=source_ids,
            conversation_id=conversation_id,
            timeout=timeout,
        )

        if result:
            return {
                "status": "success",
                "answer": result.get("answer", ""),
                "conversation_id": result.get("conversation_id"),
                "sources_used": result.get("sources_used", []),
            }
        return {"status": "error", "error": "Failed to get response"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def chat_configure(
    notebook_id: str,
    goal: str = "default",
    custom_prompt: str | None = None,
    response_length: str = "default",
) -> dict[str, Any]:
    """Configure notebook chat settings.

    Args:
        notebook_id: Notebook UUID
        goal: default|learning_guide|custom
        custom_prompt: Required when goal=custom (max 10000 chars)
        response_length: default|longer|shorter
    """
    try:
        client = get_client()

        if goal not in ("default", "learning_guide", "custom"):
            return {
                "status": "error",
                "error": f"Invalid goal '{goal}'. Use: default, learning_guide, custom",
            }

        if goal == "custom" and not custom_prompt:
            return {
                "status": "error",
                "error": "custom_prompt is required when goal='custom'",
            }

        if response_length not in ("default", "longer", "shorter"):
            return {
                "status": "error",
                "error": f"Invalid response_length '{response_length}'. Use: default, longer, shorter",
            }

        result = client.configure_chat(
            notebook_id=notebook_id,
            goal=goal,
            custom_prompt=custom_prompt,
            response_length=response_length,
        )

        if result:
            return {
                "status": "success",
                "notebook_id": notebook_id,
                "goal": goal,
                "response_length": response_length,
                "message": "Chat settings updated.",
            }
        return {"status": "error", "error": "Failed to configure chat"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
