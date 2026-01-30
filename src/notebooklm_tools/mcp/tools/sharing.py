"""Sharing tools - Notebook sharing and collaboration."""

from typing import Any

from ._utils import get_client, logged_tool


@logged_tool()
def notebook_share_status(notebook_id: str) -> dict[str, Any]:
    """Get current sharing settings and collaborators.

    Args:
        notebook_id: Notebook UUID

    Returns: is_public, access_level, collaborators list, and public_link if public
    """
    try:
        client = get_client()
        status = client.get_share_status(notebook_id)

        return {
            "status": "success",
            "notebook_id": notebook_id,
            "is_public": status.is_public,
            "access_level": status.access_level,
            "public_link": status.public_link,
            "collaborators": [
                {
                    "email": c.email,
                    "role": c.role,
                    "display_name": c.display_name,
                }
                for c in status.collaborators
            ],
            "collaborator_count": len(status.collaborators),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def notebook_share_public(
    notebook_id: str,
    is_public: bool = True,
) -> dict[str, Any]:
    """Enable or disable public link access.

    Args:
        notebook_id: Notebook UUID
        is_public: True to enable public link, False to disable (default: True)

    Returns: public_link if enabled, None if disabled
    """
    try:
        client = get_client()
        result = client.set_public_access(notebook_id, is_public)

        if is_public:
            return {
                "status": "success",
                "notebook_id": notebook_id,
                "is_public": True,
                "public_link": result,
                "message": "Public link access enabled.",
            }
        else:
            return {
                "status": "success",
                "notebook_id": notebook_id,
                "is_public": False,
                "message": "Public link access disabled.",
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
def notebook_share_invite(
    notebook_id: str,
    email: str,
    role: str = "viewer",
) -> dict[str, Any]:
    """Invite a collaborator by email.

    Args:
        notebook_id: Notebook UUID
        email: Email address to invite
        role: "viewer" or "editor" (default: viewer)

    Returns: success status
    """
    try:
        client = get_client()
        result = client.add_collaborator(notebook_id, email, role)

        if result:
            return {
                "status": "success",
                "notebook_id": notebook_id,
                "email": email,
                "role": role,
                "message": f"Invited {email} as {role}.",
            }
        return {"status": "error", "error": "Failed to invite collaborator"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
