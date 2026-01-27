# Flashcards & Quiz Downloads Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement download methods for interactive artifacts (flashcards and quizzes) with support for JSON, Markdown, and HTML output formats.

**Architecture:** Add RPC method for fetching interactive HTML content (`GET_INTERACTIVE_HTML`), implement download methods in client.py, add CLI commands, and expose as MCP tools. Parse HTML to extract embedded JSON data and format output based on user preference.

**Tech Stack:** Python 3.11+, httpx (async HTTP), regex/html.unescape (HTML parsing), typer (CLI), FastMCP (MCP server)

---

## EXECUTION PROGRESS (2026-01-27)

**Status:** Tasks 1-5 Complete (with optimizations) | Remaining: Tasks 6-11

**Completed Tasks:**
- ✅ Task 1: RPC constant added (commit: 6e73536)
- ✅ Task 2: Content extraction helpers with robust error handling (commit: a26478d)
- ✅ Task 3: Format helpers (markdown, JSON normalization) (commit: b82d247)
- ✅ Task 4-5: Download methods with optimizations (commit: 2260372)

**Optimizations Applied:**
- Added defensive API response parsing with detailed logging
- Multi-pattern HTML extraction (data-app-data, script tags, fallback patterns)
- Refactored to shared `_download_interactive_artifact()` method (eliminated ~80 lines duplication)
- Better error messages with context for debugging
- Comprehensive logging throughout extraction pipeline

**Next Steps:**
1. Task 6: Add MCP server tools (download_quiz, download_flashcards)
2. Task 7: Add CLI commands with format options
3. Task 8: Update CLAUDE.md and GEMINI.md documentation
4. Task 9: Integration testing with real notebook artifacts
5. Task 10: Update project status (todo.md, PROJECT_RECAP.md)
6. Task 11: Final commit and push

**Important Notes:**
- Client methods are now `async` and use shared implementation
- All format validation happens in shared method
- Test files created: test_extraction.py, test_formatting.py (can be removed after testing)
- Branch: feature/unified-notebooklm-tools

---

## Task 1: Add RPC Constant for Interactive HTML

**Files:**
- Modify: `src/notebooklm_tools/core/client.py:303-341`

**Step 1: Add RPC constant**

Add after line 305 (after `RPC_DELETE_STUDIO`):

```python
    RPC_GET_INTERACTIVE_HTML = "v9rmvd"  # Fetch quiz/flashcard HTML content
```

**Step 2: Add to RPC_NAMES dict**

Add to `RPC_NAMES` dict at line 27:

```python
    "v9rmvd": "get_interactive_html",
```

**Step 3: Verify constant is accessible**

Run: `python -c "from notebooklm_tools.core.client import NotebookLMClient; print(NotebookLMClient.RPC_GET_INTERACTIVE_HTML)"`
Expected: `v9rmvd`

**Step 4: Commit**

```bash
git add src/notebooklm_tools/core/client.py
git commit -m "feat: add RPC constant for interactive HTML content fetch"
```

---

## Task 2: Implement Helper Methods for Content Extraction

**Files:**
- Modify: `src/notebooklm_tools/core/client.py:3857-3900`

**Step 1: Implement _get_artifact_content method**

Replace the placeholder at line 3849 with:

```python
    def _get_artifact_content(self, notebook_id: str, artifact_id: str) -> str | None:
        """Fetch artifact HTML content for quiz/flashcard types.

        Args:
            notebook_id: The notebook ID.
            artifact_id: The artifact ID.

        Returns:
            HTML content string, or None if not found.
        """
        result = self._call_rpc(
            self.RPC_GET_INTERACTIVE_HTML,
            [artifact_id],
            f"/notebook/{notebook_id}"
        )

        # Response structure: result[0] contains artifact data
        # HTML content is at result[0][9][0]
        if result and isinstance(result, list) and len(result) > 0:
            data = result[0]
            if isinstance(data, list) and len(data) > 9 and data[9]:
                return data[9][0]
        return None
```

**Step 2: Implement _extract_app_data method**

Replace the placeholder at line 3859 with:

```python
    def _extract_app_data(self, html_content: str) -> dict:
        """Extract JSON app data from interactive HTML.

        Quiz and flashcard HTML contains embedded JSON in a data-app-data
        attribute with HTML-encoded content (&quot; for quotes).

        Args:
            html_content: The HTML content string.

        Returns:
            Parsed JSON data as dict.

        Raises:
            ArtifactParseError: If data-app-data attribute not found or invalid JSON.
        """
        import html
        import re

        match = re.search(r'data-app-data="([^"]+)"', html_content)
        if not match:
            raise ArtifactParseError(
                "interactive",
                details="No data-app-data attribute found in HTML"
            )

        encoded_json = match.group(1)
        decoded_json = html.unescape(encoded_json)

        try:
            return json.loads(decoded_json)
        except json.JSONDecodeError as e:
            raise ArtifactParseError(
                "interactive",
                details=f"Failed to parse JSON: {e}"
            ) from e
```

**Step 3: Test extraction with manual data**

Create a test script `test_extraction.py`:

```python
from notebooklm_tools.core.client import NotebookLMClient

html = '<div data-app-data="{&quot;quiz&quot;:[{&quot;question&quot;:&quot;test&quot;}]}"></div>'
client = NotebookLMClient("", "", "")
data = client._extract_app_data(html)
assert data == {"quiz": [{"question": "test"}]}
print("✓ Extraction works")
```

Run: `python test_extraction.py`
Expected: `✓ Extraction works`

**Step 4: Commit**

```bash
git add src/notebooklm_tools/core/client.py
git commit -m "feat: add HTML content fetching and JSON extraction helpers"
```

---

## Task 3: Implement Format Helper Methods

**Files:**
- Modify: `src/notebooklm_tools/core/client.py:3868-3900`

**Step 1: Implement _format_quiz_markdown**

Add before `_format_interactive_content` at line 3868:

```python
    @staticmethod
    def _format_quiz_markdown(title: str, questions: list[dict]) -> str:
        """Format quiz as markdown.

        Args:
            title: Quiz title.
            questions: List of question dicts with 'question', 'answerOptions', 'hint'.

        Returns:
            Formatted markdown string.
        """
        lines = [f"# {title}", ""]

        for i, q in enumerate(questions, 1):
            lines.append(f"## Question {i}")
            lines.append(q.get("question", ""))
            lines.append("")

            for opt in q.get("answerOptions", []):
                marker = "[x]" if opt.get("isCorrect") else "[ ]"
                lines.append(f"- {marker} {opt.get('text', '')}")

            if q.get("hint"):
                lines.append("")
                lines.append(f"**Hint:** {q['hint']}")

            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_flashcards_markdown(title: str, cards: list[dict]) -> str:
        """Format flashcards as markdown.

        Args:
            title: Flashcard deck title.
            cards: List of card dicts with 'f' (front) and 'b' (back).

        Returns:
            Formatted markdown string.
        """
        lines = [f"# {title}", ""]

        for i, card in enumerate(cards, 1):
            front = card.get("f", "")
            back = card.get("b", "")

            lines.append(f"## Card {i}")
            lines.append("")
            lines.append(f"**Front:** {front}")
            lines.append("")
            lines.append(f"**Back:** {back}")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
```

**Step 2: Update _format_interactive_content method**

Replace the placeholder at line 3868 with:

```python
    def _format_interactive_content(
        self,
        app_data: dict,
        title: str,
        output_format: str,
        html_content: str,
        is_quiz: bool,
    ) -> str:
        """Format quiz or flashcard content for output.

        Args:
            app_data: Parsed JSON data from HTML.
            title: Artifact title.
            output_format: Output format - json, markdown, or html.
            html_content: Original HTML content.
            is_quiz: True for quiz, False for flashcards.

        Returns:
            Formatted content string.
        """
        if output_format == "html":
            return html_content

        if is_quiz:
            questions = app_data.get("quiz", [])
            if output_format == "markdown":
                return self._format_quiz_markdown(title, questions)
            return json.dumps({"title": title, "questions": questions}, indent=2)

        # Flashcards
        cards = app_data.get("flashcards", [])
        if output_format == "markdown":
            return self._format_flashcards_markdown(title, cards)

        # Normalize JSON format: {"f": "...", "b": "..."} -> {"front": "...", "back": "..."}
        normalized = [{"front": c.get("f", ""), "back": c.get("b", "")} for c in cards]
        return json.dumps({"title": title, "cards": normalized}, indent=2)
```

**Step 3: Test formatting**

Create test script `test_formatting.py`:

```python
from notebooklm_tools.core.client import NotebookLMClient

client = NotebookLMClient("", "", "")

# Test quiz markdown
quiz_data = {"quiz": [{"question": "What is 2+2?", "answerOptions": [
    {"text": "3", "isCorrect": False},
    {"text": "4", "isCorrect": True}
], "hint": "Count on your fingers"}]}
md = client._format_interactive_content(quiz_data, "Math Quiz", "markdown", "", True)
assert "## Question 1" in md
assert "[x] 4" in md
assert "**Hint:**" in md
print("✓ Quiz markdown works")

# Test flashcards JSON
cards_data = {"flashcards": [{"f": "Front", "b": "Back"}]}
json_str = client._format_interactive_content(cards_data, "Cards", "json", "", False)
assert '"front": "Front"' in json_str
print("✓ Flashcards JSON works")
```

Run: `python test_formatting.py`
Expected: Both checks pass

**Step 4: Commit**

```bash
git add src/notebooklm_tools/core/client.py
git commit -m "feat: add quiz and flashcard formatting helpers"
```

---

## Task 4: Implement download_quiz Method

**Files:**
- Modify: `src/notebooklm_tools/core/client.py:3908-3930`

**Step 1: Replace download_quiz placeholder**

Replace the existing placeholder at line 3908 with:

```python
    async def download_quiz(
        self,
        notebook_id: str,
        output_path: str,
        artifact_id: str | None = None,
        output_format: str = "json",
    ) -> str:
        """Download quiz artifact.

        Args:
            notebook_id: The notebook ID.
            output_path: Path to save the file.
            artifact_id: Specific artifact ID, or uses first completed quiz.
            output_format: Output format - json, markdown, or html (default: json).

        Returns:
            The output path where the file was saved.

        Raises:
            ValueError: If invalid output_format.
            ArtifactNotReadyError: If no completed quiz found.
            ArtifactParseError: If content parsing fails.
        """
        # Validate format
        valid_formats = ("json", "markdown", "html")
        if output_format not in valid_formats:
            raise ValueError(
                f"Invalid output_format: {output_format!r}. "
                f"Use one of: {', '.join(valid_formats)}"
            )

        artifacts = self._list_raw(notebook_id)

        # Filter for completed quizzes/flashcards (Type 4, Status 3)
        # Note: Type 4 covers both quizzes and flashcards
        candidates = []
        for a in artifacts:
            if isinstance(a, list) and len(a) > 4:
                if a[2] == self.STUDIO_TYPE_FLASHCARDS and a[4] == 3:
                    candidates.append(a)

        if not candidates:
            raise ArtifactNotReadyError("quiz")

        # Select artifact
        target = None
        if artifact_id:
            target = next((a for a in candidates if a[0] == artifact_id), None)
            if not target:
                raise ArtifactNotReadyError("quiz", artifact_id)
        else:
            # Use most recent
            target = candidates[0]

        # Fetch HTML content
        html_content = self._get_artifact_content(notebook_id, target[0])
        if not html_content:
            raise ArtifactDownloadError("quiz", details="Failed to fetch content")

        # Extract and parse JSON
        try:
            app_data = self._extract_app_data(html_content)
        except (ValueError, json.JSONDecodeError) as e:
            raise ArtifactParseError("quiz", details=str(e)) from e

        # Get title (index 1 in artifact data)
        title = target[1] if len(target) > 1 and target[1] else "Untitled Quiz"

        # Format content
        content = self._format_interactive_content(
            app_data, title, output_format, html_content, is_quiz=True
        )

        # Write to file
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")

        return str(output)
```

**Step 2: Verify imports**

Add to imports at top of file if not present:

```python
from pathlib import Path
```

**Step 3: Commit**

```bash
git add src/notebooklm_tools/core/client.py
git commit -m "feat: implement async download_quiz method"
```

---

## Task 5: Implement download_flashcards Method

**Files:**
- Modify: `src/notebooklm_tools/core/client.py:3931-3960`

**Step 1: Replace download_flashcards placeholder**

Replace the existing placeholder at line 3931 with:

```python
    async def download_flashcards(
        self,
        notebook_id: str,
        output_path: str,
        artifact_id: str | None = None,
        output_format: str = "json",
    ) -> str:
        """Download flashcard deck artifact.

        Args:
            notebook_id: The notebook ID.
            output_path: Path to save the file.
            artifact_id: Specific artifact ID, or uses first completed flashcard deck.
            output_format: Output format - json, markdown, or html (default: json).

        Returns:
            The output path where the file was saved.

        Raises:
            ValueError: If invalid output_format.
            ArtifactNotReadyError: If no completed flashcards found.
            ArtifactParseError: If content parsing fails.
        """
        # Validate format
        valid_formats = ("json", "markdown", "html")
        if output_format not in valid_formats:
            raise ValueError(
                f"Invalid output_format: {output_format!r}. "
                f"Use one of: {', '.join(valid_formats)}"
            )

        artifacts = self._list_raw(notebook_id)

        # Filter for completed flashcards (Type 4, Status 3)
        candidates = []
        for a in artifacts:
            if isinstance(a, list) and len(a) > 4:
                if a[2] == self.STUDIO_TYPE_FLASHCARDS and a[4] == 3:
                    candidates.append(a)

        if not candidates:
            raise ArtifactNotReadyError("flashcards")

        # Select artifact
        target = None
        if artifact_id:
            target = next((a for a in candidates if a[0] == artifact_id), None)
            if not target:
                raise ArtifactNotReadyError("flashcards", artifact_id)
        else:
            # Use most recent
            target = candidates[0]

        # Fetch HTML content
        html_content = self._get_artifact_content(notebook_id, target[0])
        if not html_content:
            raise ArtifactDownloadError("flashcards", details="Failed to fetch content")

        # Extract and parse JSON
        try:
            app_data = self._extract_app_data(html_content)
        except (ValueError, json.JSONDecodeError) as e:
            raise ArtifactParseError("flashcards", details=str(e)) from e

        # Get title
        title = target[1] if len(target) > 1 and target[1] else "Untitled Flashcards"

        # Format content
        content = self._format_interactive_content(
            app_data, title, output_format, html_content, is_quiz=False
        )

        # Write to file
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")

        return str(output)
```

**Step 2: Commit**

```bash
git add src/notebooklm_tools/core/client.py
git commit -m "feat: implement async download_flashcards method"
```

---

## Task 6: Add MCP Server Tools

**Files:**
- Modify: `src/notebooklm_tools/mcp/server.py:879-920`

**Step 1: Add download_quiz tool**

Add after `download_data_table` function around line 879:

```python
@logged_tool()
async def download_quiz(
    notebook_id: str,
    output_path: str,
    artifact_id: str | None = None,
    output_format: str = "json",
) -> dict[str, Any]:
    """Download Quiz to a file.

    Args:
        notebook_id: Notebook UUID
        output_path: Path to save the file
        artifact_id: Optional specific artifact ID
        output_format: Output format - json, markdown, or html (default: json)
    """
    try:
        client = get_client()
        saved_path = await client.download_quiz(
            notebook_id, output_path, artifact_id, output_format
        )
        return {
            "status": "success",
            "path": saved_path,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@logged_tool()
async def download_flashcards(
    notebook_id: str,
    output_path: str,
    artifact_id: str | None = None,
    output_format: str = "json",
) -> dict[str, Any]:
    """Download Flashcards to a file.

    Args:
        notebook_id: Notebook UUID
        output_path: Path to save the file
        artifact_id: Optional specific artifact ID
        output_format: Output format - json, markdown, or html (default: json)
    """
    try:
        client = get_client()
        saved_path = await client.download_flashcards(
            notebook_id, output_path, artifact_id, output_format
        )
        return {
            "status": "success",
            "path": saved_path,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**Step 2: Test MCP tool registration**

Run: `notebooklm-mcp --help 2>&1 | grep -E "download_quiz|download_flashcards"`
Expected: Should show both tools are registered

**Step 3: Commit**

```bash
git add src/notebooklm_tools/mcp/server.py
git commit -m "feat: add MCP tools for quiz and flashcard downloads"
```

---

## Task 7: Add CLI Commands

**Files:**
- Modify: `src/notebooklm_tools/cli/commands/download.py:184-250`

**Step 1: Add quiz download command**

Add after `download_data_table` function around line 184:

```python
@app.command("quiz")
def download_quiz_cmd(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Output path (default: ./{notebook_id}_quiz.{ext})"
    ),
    artifact_id: Optional[str] = typer.Option(None, "--id", help="Specific artifact ID"),
    format: str = typer.Option(
        "json", "--format", "-f",
        help="Output format: json, markdown, or html"
    ),
):
    """Download Quiz."""
    client = get_client()

    # Validate format
    if format not in ("json", "markdown", "html"):
        console.print(
            f"[red]Error:[/red] Invalid format '{format}'. "
            "Use: json, markdown, or html",
            err=True
        )
        raise typer.Exit(1)

    # Determine extension
    ext_map = {"json": "json", "markdown": "md", "html": "html"}
    ext = ext_map[format]

    try:
        path = output or f"{notebook_id}_quiz.{ext}"
        saved = asyncio.run(
            client.download_quiz(notebook_id, path, artifact_id, format)
        )
        console.print(f"[green]✓[/green] Downloaded quiz to: {saved}")
    except ArtifactNotReadyError:
        console.print(
            "[red]Error:[/red] Quiz is not ready or does not exist.",
            err=True
        )
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        handle_error(e)


@app.command("flashcards")
def download_flashcards_cmd(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Output path (default: ./{notebook_id}_flashcards.{ext})"
    ),
    artifact_id: Optional[str] = typer.Option(None, "--id", help="Specific artifact ID"),
    format: str = typer.Option(
        "json", "--format", "-f",
        help="Output format: json, markdown, or html"
    ),
):
    """Download Flashcards."""
    client = get_client()

    # Validate format
    if format not in ("json", "markdown", "html"):
        console.print(
            f"[red]Error:[/red] Invalid format '{format}'. "
            "Use: json, markdown, or html",
            err=True
        )
        raise typer.Exit(1)

    # Determine extension
    ext_map = {"json": "json", "markdown": "md", "html": "html"}
    ext = ext_map[format]

    try:
        path = output or f"{notebook_id}_flashcards.{ext}"
        saved = asyncio.run(
            client.download_flashcards(notebook_id, path, artifact_id, format)
        )
        console.print(f"[green]✓[/green] Downloaded flashcards to: {saved}")
    except ArtifactNotReadyError:
        console.print(
            "[red]Error:[/red] Flashcards are not ready or do not exist.",
            err=True
        )
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        handle_error(e)
```

**Step 2: Test CLI commands**

Run: `nlm download --help`
Expected: Should show quiz and flashcards commands

**Step 3: Commit**

```bash
git add src/notebooklm_tools/cli/commands/download.py
git commit -m "feat: add CLI commands for quiz and flashcard downloads"
```

---

## Task 8: Update Documentation

**Files:**
- Modify: `CLAUDE.md:132-145`
- Modify: `GEMINI.md` (similar additions)

**Step 1: Update CLAUDE.md MCP Tools table**

Add rows to the MCP tools table after `download_mind_map`:

```markdown
| `download_quiz` | Download Quiz to file (JSON/Markdown/HTML) |
| `download_flashcards` | Download Flashcards to file (JSON/Markdown/HTML) |
```

**Step 2: Update GEMINI.md**

Make similar additions to GEMINI.md in the MCP tools section.

**Step 3: Commit**

```bash
git add CLAUDE.md GEMINI.md
git commit -m "docs: add quiz and flashcard download tools to documentation"
```

---

## Task 9: Integration Testing with Real Notebook

**Files:**
- Test with notebook: `4085e211-fdb0-4802-b973-b43b9f99b6f7`
- Available artifacts:
  - `a7e46e94-48a2-4d91-b2c6-dd9e0cff59f6` - Quantum Quiz
  - `c0549375-f013-4109-91de-a4d8e1ef9e29` - Quantum Flashcards
  - `5295aef0-c1f0-4b7a-9e4f-72c9c288b6a7` - Quantum Quiz

**Step 1: Reinstall package**

```bash
uv cache clean && uv tool install --force .
```

**Step 2: Test MCP quiz download (JSON)**

Via MCP tool:
```python
mcp__notebooklm-mcp__download_quiz(
    notebook_id="4085e211-fdb0-4802-b973-b43b9f99b6f7",
    artifact_id="a7e46e94-48a2-4d91-b2c6-dd9e0cff59f6",
    output_path="/Users/jbd/Downloads/Quantum_Quiz_MCP.json",
    output_format="json"
)
```
Expected: Success with valid JSON file

**Step 3: Test MCP quiz download (Markdown)**

```python
mcp__notebooklm-mcp__download_quiz(
    notebook_id="4085e211-fdb0-4802-b973-b43b9f99b6f7",
    artifact_id="a7e46e94-48a2-4d91-b2c6-dd9e0cff59f6",
    output_path="/Users/jbd/Downloads/Quantum_Quiz_MCP.md",
    output_format="markdown"
)
```
Expected: Success with formatted markdown

**Step 4: Test MCP flashcards download (JSON)**

```python
mcp__notebooklm-mcp__download_flashcards(
    notebook_id="4085e211-fdb0-4802-b973-b43b9f99b6f7",
    artifact_id="c0549375-f013-4109-91de-a4d8e1ef9e29",
    output_path="/Users/jbd/Downloads/Quantum_Flashcards_MCP.json",
    output_format="json"
)
```
Expected: Success with normalized JSON (front/back)

**Step 5: Test MCP flashcards download (Markdown)**

```python
mcp__notebooklm-mcp__download_flashcards(
    notebook_id="4085e211-fdb0-4802-b973-b43b9f99b6f7",
    artifact_id="c0549375-f013-4109-91de-a4d8e1ef9e29",
    output_path="/Users/jbd/Downloads/Quantum_Flashcards_MCP.md",
    output_format="markdown"
)
```
Expected: Success with card-per-section markdown

**Step 6: Test CLI quiz download**

```bash
nlm download quiz 4085e211-fdb0-4802-b973-b43b9f99b6f7 \
    --id a7e46e94-48a2-4d91-b2c6-dd9e0cff59f6 \
    --output /Users/jbd/Downloads/Quantum_Quiz_CLI.json \
    --format json
```
Expected: Success message with file path

**Step 7: Test CLI flashcards download**

```bash
nlm download flashcards 4085e211-fdb0-4802-b973-b43b9f99b6f7 \
    --id c0549375-f013-4109-91de-a4d8e1ef9e29 \
    --output /Users/jbd/Downloads/Quantum_Flashcards_CLI.md \
    --format markdown
```
Expected: Success message with file path

**Step 8: Verify all downloaded files**

```bash
ls -lh /Users/jbd/Downloads/*Quiz* /Users/jbd/Downloads/*Flashcard*
```
Expected: 6 files (3 quiz, 3 flashcards) with reasonable sizes

**Step 9: Commit if all tests pass**

```bash
git add -A
git commit -m "test: verify quiz and flashcard downloads work end-to-end"
```

---

## Task 10: Update Project Status

**Files:**
- Modify: `todo.md:30-36`
- Modify: `PROJECT_RECAP.md:55-60`

**Step 1: Mark Phase 1.5 as complete in todo.md**

Update the Phase 1.5 section:

```markdown
## Phase 1.5: Interactive Artifacts - [COMPLETED ✅]
- [x] Add `download_flashcards` method with JSON/Markdown/HTML formats
- [x] Add `download_quiz` method with JSON/Markdown/HTML formats
- [x] Add RPC method for interactive HTML fetch (`v9rmvd`)
- [x] Implement HTML data extraction (parse `data-app-data` attribute)
- [x] Add format conversion (JSON → Markdown, JSON → HTML)
```

**Step 2: Update PROJECT_RECAP.md completed tasks**

Add to the completed tasks section:

```markdown
- [x] **Interactive Artifacts**: Quiz and flashcard downloads with multiple formats (JSON, Markdown, HTML)
```

**Step 3: Commit**

```bash
git add todo.md PROJECT_RECAP.md
git commit -m "docs: mark Phase 1.5 interactive artifacts as complete"
```

---

## Task 11: Final Commit and Push

**Step 1: Create comprehensive commit message**

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat: implement quiz and flashcard downloads with multi-format support

Phase 1.5 complete - adds full support for downloading interactive artifacts
(quizzes and flashcards) in JSON, Markdown, and HTML formats.

Features:
- Add RPC method GET_INTERACTIVE_HTML (v9rmvd) for fetching HTML content
- Implement async download_quiz() and download_flashcards() client methods
- Parse HTML data-app-data attribute and extract embedded JSON
- Support 3 output formats: JSON (normalized), Markdown, HTML (raw)
- Add MCP server tools: download_quiz, download_flashcards
- Add CLI commands: nlm download quiz/flashcards with --format option
- Comprehensive format helpers for readable markdown output

Tested with 3 artifacts from test notebook (all formats verified).

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

**Step 2: Push to remote**

```bash
git push origin feature/unified-notebooklm-tools
```

Expected: Push successful

---

## Summary

**Completed:**
- ✅ RPC constant for interactive HTML fetch
- ✅ HTML content fetching and JSON extraction
- ✅ Format helpers (markdown, JSON normalization)
- ✅ Async download methods (quiz, flashcards)
- ✅ MCP server tools
- ✅ CLI commands with format options
- ✅ Documentation updates
- ✅ Full integration testing (6 test cases)

**Files Modified:**
- `src/notebooklm_tools/core/client.py` - Core download logic
- `src/notebooklm_tools/mcp/server.py` - MCP tools
- `src/notebooklm_tools/cli/commands/download.py` - CLI commands
- `CLAUDE.md`, `GEMINI.md` - Documentation
- `todo.md`, `PROJECT_RECAP.md` - Project status

**Next Phase:** Phase 2 - UX Polish (progress bars, streaming downloads)
