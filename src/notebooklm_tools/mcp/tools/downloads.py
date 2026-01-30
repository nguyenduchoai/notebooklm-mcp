"""Download tools - Consolidated download_artifact for all artifact types."""

from typing import Any, Literal

from ._utils import get_client, logged_tool

# Supported artifact types and their formats
ARTIFACT_TYPES = Literal[
    "audio",
    "video", 
    "report",
    "mind_map",
    "slide_deck",
    "infographic",
    "data_table",
    "quiz",
    "flashcards",
]

# Output formats for interactive artifacts
OUTPUT_FORMATS = Literal["json", "markdown", "html"]


@logged_tool()
async def download_artifact(
    notebook_id: str,
    artifact_type: str,
    output_path: str,
    artifact_id: str | None = None,
    output_format: str = "json",
) -> dict[str, Any]:
    """Download any NotebookLM artifact to a file.

    Unified download tool replacing 9 separate download tools.
    Supports all artifact types: audio, video, report, mind_map, slide_deck,
    infographic, data_table, quiz, flashcards.

    Args:
        notebook_id: Notebook UUID
        artifact_type: Type of artifact to download:
            - audio: Audio Overview (MP4/MP3)
            - video: Video Overview (MP4)
            - report: Report (Markdown)
            - mind_map: Mind Map (JSON)
            - slide_deck: Slide Deck (PDF)
            - infographic: Infographic (PNG)
            - data_table: Data Table (CSV)
            - quiz: Quiz (json|markdown|html)
            - flashcards: Flashcards (json|markdown|html)
        output_path: Path to save the file
        artifact_id: Optional specific artifact ID (uses latest if not provided)
        output_format: For quiz/flashcards only: json|markdown|html (default: json)

    Returns:
        dict with status and saved file path

    Example:
        download_artifact(notebook_id="abc123", artifact_type="audio", output_path="podcast.mp3")
        download_artifact(notebook_id="abc123", artifact_type="quiz", output_path="quiz.html", output_format="html")
    """
    valid_types = [
        "audio", "video", "report", "mind_map", "slide_deck",
        "infographic", "data_table", "quiz", "flashcards"
    ]
    
    if artifact_type not in valid_types:
        return {
            "status": "error",
            "error": f"Unknown artifact_type '{artifact_type}'. Valid types: {', '.join(valid_types)}",
        }
    
    try:
        client = get_client()
        saved_path = None
        
        # Route to appropriate download method
        if artifact_type == "audio":
            saved_path = await client.download_audio(
                notebook_id, output_path, artifact_id, progress_callback=None
            )
        elif artifact_type == "video":
            saved_path = await client.download_video(
                notebook_id, output_path, artifact_id, progress_callback=None
            )
        elif artifact_type == "report":
            saved_path = client.download_report(notebook_id, output_path, artifact_id)
        elif artifact_type == "mind_map":
            saved_path = client.download_mind_map(notebook_id, output_path, artifact_id)
        elif artifact_type == "slide_deck":
            saved_path = await client.download_slide_deck(
                notebook_id, output_path, artifact_id, progress_callback=None
            )
        elif artifact_type == "infographic":
            saved_path = await client.download_infographic(
                notebook_id, output_path, artifact_id, progress_callback=None
            )
        elif artifact_type == "data_table":
            saved_path = client.download_data_table(notebook_id, output_path, artifact_id)
        elif artifact_type == "quiz":
            if output_format not in ("json", "markdown", "html"):
                return {
                    "status": "error",
                    "error": f"Invalid output_format '{output_format}'. Use: json, markdown, html",
                }
            saved_path = await client.download_quiz(
                notebook_id, output_path, artifact_id, output_format
            )
        elif artifact_type == "flashcards":
            if output_format not in ("json", "markdown", "html"):
                return {
                    "status": "error",
                    "error": f"Invalid output_format '{output_format}'. Use: json, markdown, html",
                }
            saved_path = await client.download_flashcards(
                notebook_id, output_path, artifact_id, output_format
            )
        else:
            return {"status": "error", "error": f"Unhandled artifact type: {artifact_type}"}
        
        return {
            "status": "success",
            "artifact_type": artifact_type,
            "path": saved_path,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

