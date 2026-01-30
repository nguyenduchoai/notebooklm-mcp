"""Notes tools - Note management operations."""

from typing import Any
from ._utils import get_client, logged_tool


@logged_tool()
def note_create(
    notebook_id: str,
    content: str,
    title: str | None = None,
) -> dict[str, Any]:
    """Create a note in a notebook.

    Args:
        notebook_id: Notebook UUID
        content: Note content (text)
        title: Optional title for the note

    Returns: note_id, title, created_at
    """
    try:
        client = get_client()
        result = client.create_note(notebook_id, content, title)

        if result and result.get("id"):
            return {
                "status": "success",
                "note_id": result["id"],
                "title": result.get("title", ""),
                "content_preview": content[:100] if len(content) > 100 else content,
            }
        return {"status": "error", "error": "Failed to create note"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def note_list(notebook_id: str) -> dict[str, Any]:
    """List all notes in a notebook.

    Args:
        notebook_id: Notebook UUID

    Returns: Array of notes with id, title, content preview
    """
    try:
        client = get_client()
        notes = client.list_notes(notebook_id)

        return {
            "status": "success",
            "notebook_id": notebook_id,
            "notes": notes,
            "count": len(notes),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def note_update(
    notebook_id: str,
    note_id: str,
    content: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Update a note's content or title.

    Args:
        notebook_id: Notebook UUID
        note_id: Note UUID
        content: New content (optional)
        title: New title (optional)

    Returns: Updated note details
    """
    if content is None and title is None:
        return {"status": "error", "error": "Must provide content or title to update"}

    try:
        client = get_client()
        result = client.update_note(note_id, content, title, notebook_id)

        if result:
            return {
                "status": "success",
                "note_id": note_id,
                "updated": True,
            }
        return {"status": "error", "error": "Failed to update note"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def note_delete(notebook_id: str, note_id: str, confirm: bool = False) -> dict[str, Any]:
    """Delete a note permanently. IRREVERSIBLE. Requires confirm=True.

    Args:
        notebook_id: Notebook UUID
        note_id: Note UUID
        confirm: Must be True after user approval
    """
    if not confirm:
        return {
            "status": "error",
            "error": "Deletion not confirmed. Set confirm=True after user approval.",
            "warning": "This action is IRREVERSIBLE.",
        }

    try:
        client = get_client()
        result = client.delete_note(note_id, notebook_id)

        if result:
            return {
                "status": "success",
                "message": f"Note {note_id} has been permanently deleted.",
            }
        return {"status": "error", "error": "Failed to delete note"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
