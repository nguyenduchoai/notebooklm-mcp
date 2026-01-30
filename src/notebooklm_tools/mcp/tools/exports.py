"""Export tools - Export artifacts to Google Docs/Sheets."""

from typing import Any

from ._utils import get_client, logged_tool


@logged_tool()
def export_artifact(
    notebook_id: str,
    artifact_id: str,
    export_type: str,
    title: str | None = None,
) -> dict[str, Any]:
    """Export a NotebookLM artifact to Google Docs or Sheets.

    Supports:
    - Data Tables → Google Sheets
    - Reports (Briefing Doc, Study Guide, Blog Post) → Google Docs

    Args:
        notebook_id: Notebook UUID
        artifact_id: Artifact UUID to export
        export_type: "docs" or "sheets"
        title: Title for exported document (optional)

    Returns: URL to the created Google Doc/Sheet
    """
    try:
        client = get_client()
        
        result = client.export_artifact(
            notebook_id=notebook_id,
            artifact_id=artifact_id,
            title=title or "NotebookLM Export",
            export_type=export_type,
        )

        if result.get("url"):
            export_type_label = "Google Docs" if export_type == "docs" else "Google Sheets"
            return {
                "status": "success",
                "notebook_id": notebook_id,
                "artifact_id": artifact_id,
                "export_type": export_type,
                "url": result["url"],
                "message": f"Exported to {export_type_label}: {result['url']}",
            }
        else:
            return {
                "status": "error",
                "error": result.get("message", "Export failed - no document URL returned"),
            }
    except ValueError as e:
        # Invalid export type
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
