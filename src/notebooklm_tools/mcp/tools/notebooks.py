"""Notebook tools - Notebook management operations."""

from typing import Any

from ._utils import get_client, logged_tool


@logged_tool()
def notebook_list(max_results: int = 100) -> dict[str, Any]:
    """List all notebooks.

    Args:
        max_results: Maximum number of notebooks to return (default: 100)
    """
    try:
        client = get_client()
        notebooks = client.list_notebooks()

        # Count owned vs shared notebooks
        owned_count = sum(1 for nb in notebooks if nb.is_owned)
        shared_count = len(notebooks) - owned_count
        shared_by_me_count = sum(1 for nb in notebooks if nb.is_owned and nb.is_shared)

        return {
            "status": "success",
            "count": len(notebooks),
            "owned_count": owned_count,
            "shared_count": shared_count,
            "shared_by_me_count": shared_by_me_count,
            "notebooks": [
                {
                    "id": nb.id,
                    "title": nb.title,
                    "source_count": nb.source_count,
                    "url": nb.url,
                    "ownership": nb.ownership,
                    "is_shared": nb.is_shared,
                    "created_at": nb.created_at,
                    "modified_at": nb.modified_at,
                }
                for nb in notebooks[:max_results]
            ],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def notebook_get(notebook_id: str) -> dict[str, Any]:
    """Get notebook details with sources.

    Args:
        notebook_id: Notebook UUID
    """
    try:
        client = get_client()
        nb = client.get_notebook(notebook_id)

        if nb:
            # Client returns raw RPC data (list), not a Notebook object
            # Structure: [[title, sources, id, emoji, null, metadata, ...]]
            if isinstance(nb, list):
                # Handle nested list structure
                data = nb[0] if nb and isinstance(nb[0], list) else nb
                if isinstance(data, list) and len(data) >= 3:
                    title = data[0] if isinstance(data[0], str) else "Untitled"
                    sources_data = data[1] if len(data) > 1 and isinstance(data[1], list) else []
                    nb_id = data[2] if len(data) > 2 else notebook_id
                    
                    sources = []
                    for src in sources_data:
                        if isinstance(src, list) and len(src) >= 2:
                            src_id = src[0][0] if isinstance(src[0], list) and src[0] else src[0]
                            src_title = src[1] if len(src) > 1 else "Untitled"
                            sources.append({"id": src_id, "title": src_title})
                    
                    return {
                        "status": "success",
                        "notebook": {
                            "id": nb_id,
                            "title": title,
                            "source_count": len(sources),
                            "url": f"https://notebooklm.google.com/notebook/{nb_id}",
                        },
                        "sources": sources,
                    }
            # Fallback: return raw data
            return {"status": "success", "notebook_id": notebook_id, "raw": str(nb)[:500]}
        return {"status": "error", "error": "Notebook not found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def notebook_describe(notebook_id: str) -> dict[str, Any]:
    """Get AI-generated notebook summary with suggested topics.

    Args:
        notebook_id: Notebook UUID

    Returns: summary (markdown), suggested_topics list
    """
    try:
        client = get_client()
        result = client.get_notebook_summary(notebook_id)

        if result:
            return {
                "status": "success",
                "summary": result.get("summary", ""),
                "suggested_topics": result.get("suggested_topics", []),
            }
        return {"status": "error", "error": "Failed to get notebook summary"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def notebook_create(title: str = "") -> dict[str, Any]:
    """Create a new notebook.

    Args:
        title: Optional title for the notebook
    """
    try:
        client = get_client()
        nb = client.create_notebook(title)

        if nb:
            return {
                "status": "success",
                "notebook_id": nb.id,  # Also at root for convenience
                "notebook": {
                    "id": nb.id,
                    "title": nb.title,
                    "url": nb.url,
                },
                "message": f"Created notebook: {nb.title}",
            }
        return {"status": "error", "error": "Failed to create notebook"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def notebook_rename(notebook_id: str, new_title: str) -> dict[str, Any]:
    """Rename a notebook.

    Args:
        notebook_id: Notebook UUID
        new_title: New title
    """
    try:
        client = get_client()
        result = client.rename_notebook(notebook_id, new_title)

        if result:
            return {
                "status": "success",
                "notebook_id": notebook_id,
                "new_title": new_title,
                "message": f"Renamed notebook to: {new_title}",
            }
        return {"status": "error", "error": "Failed to rename notebook"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def notebook_delete(notebook_id: str, confirm: bool = False) -> dict[str, Any]:
    """Delete notebook permanently. IRREVERSIBLE. Requires confirm=True.

    Args:
        notebook_id: Notebook UUID
        confirm: Must be True after user approval
    """
    if not confirm:
        return {
            "status": "error",
            "error": "Deletion not confirmed. You must ask the user to confirm "
            "before deleting. Set confirm=True only after user approval.",
            "warning": "This action is IRREVERSIBLE. The notebook and all its contents will be permanently deleted.",
        }

    try:
        client = get_client()
        result = client.delete_notebook(notebook_id)

        if result:
            return {
                "status": "success",
                "message": f"Notebook {notebook_id} has been permanently deleted.",
            }
        return {"status": "error", "error": "Failed to delete notebook"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
