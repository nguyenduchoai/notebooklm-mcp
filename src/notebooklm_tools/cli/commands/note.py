"""Note CLI commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from notebooklm_tools.core.alias import get_alias_manager
from notebooklm_tools.core.exceptions import NLMError
from notebooklm_tools.cli.utils import get_client

console = Console()
app = typer.Typer(
    help="Manage notes",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


@app.command("list")
def list_notes(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Output IDs only"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """List all notes in a notebook."""
    try:
        notebook_id = get_alias_manager().resolve(notebook_id)
        with get_client(profile) as client:
            notes = client.list_notes(notebook_id)

        if quiet:
            for note in notes:
                console.print(note['id'])
        elif json_output:
            import json
            console.print(json.dumps(notes, indent=2))
        else:
            if not notes:
                console.print(f"[dim]No notes found in notebook {notebook_id}[/dim]")
                return

            table = Table(title=f"Notes in Notebook {notebook_id}")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="green")
            table.add_column("Preview", style="white")

            for note in notes:
                preview = note.get('preview', '')[:100]
                if len(preview) == 100:
                    preview += "..."
                table.add_row(note['id'][:8] + "...", note.get('title', 'Untitled'), preview)

            console.print(table)
            console.print(f"\n[dim]Total: {len(notes)} note(s)[/dim]")
    except NLMError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"\n[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)


@app.command("create")
def create_note(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    content: str = typer.Option(..., "--content", "-c", help="Note content"),
    title: str = typer.Option("New Note", "--title", "-t", help="Note title"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Create a new note in a notebook."""
    try:
        notebook_id = get_alias_manager().resolve(notebook_id)
        with get_client(profile) as client:
            result = client.create_note(notebook_id, content, title)

        if result:
            console.print(f"[green]✓[/green] Note created: {result['id']}")
            console.print(f"  Title: {result['title']}")
            console.print(f"  Preview: {result.get('content', '')[:100]}...")
        else:
            console.print("[red]Failed to create note[/red]")
            raise typer.Exit(1)
    except NLMError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"\n[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)


@app.command("update")
def update_note(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    note_id: str = typer.Argument(..., help="Note ID"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="New content"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Update a note's content or title."""
    if not content and not title:
        console.print("[red]Error:[/red] Must provide --content or --title")
        raise typer.Exit(1)

    try:
        notebook_id = get_alias_manager().resolve(notebook_id)
        with get_client(profile) as client:
            result = client.update_note(note_id, content, title, notebook_id)

        if result:
            console.print(f"[green]✓[/green] Note updated: {note_id}")
            if title:
                console.print(f"  New title: {title}")
            if content:
                console.print(f"  Content updated ({len(content)} chars)")
        else:
            console.print("[red]Failed to update note[/red]")
            raise typer.Exit(1)
    except NLMError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"\n[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)


@app.command("delete")
def delete_note(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    note_id: str = typer.Argument(..., help="Note ID to delete"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Skip confirmation"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Delete a note permanently."""
    if not confirm:
        confirmed = typer.confirm(f"Delete note {note_id}? This action is IRREVERSIBLE.")
        if not confirmed:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    try:
        notebook_id = get_alias_manager().resolve(notebook_id)
        with get_client(profile) as client:
            result = client.delete_note(note_id, notebook_id)

        if result:
            console.print(f"[green]✓[/green] Note deleted: {note_id}")
        else:
            console.print("[red]Failed to delete note[/red]")
            raise typer.Exit(1)
    except NLMError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"\n[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)
