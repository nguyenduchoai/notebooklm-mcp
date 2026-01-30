"""Sharing CLI commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from notebooklm_tools.core.alias import get_alias_manager
from notebooklm_tools.core.exceptions import NLMError
from notebooklm_tools.cli.utils import get_client

console = Console()
app = typer.Typer(
    help="Manage notebook sharing",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


@app.command("status")
def share_status(
    notebook: str = typer.Argument(..., help="Notebook ID or alias"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Show sharing status and collaborators."""
    try:
        notebook_id = get_alias_manager().resolve(notebook)
        with get_client(profile) as client:
            status = client.get_share_status(notebook_id)
        
        if json_output:
            import json
            data = {
                "is_public": status.is_public,
                "access_level": status.access_level,
                "public_link": status.public_link,
                "collaborators": [
                    {
                        "email": c.email,
                        "role": c.role,
                        "is_pending": c.is_pending,
                        "display_name": c.display_name,
                    }
                    for c in status.collaborators
                ],
            }
            console.print(json.dumps(data, indent=2))
            return
        
        # Rich output
        console.print(f"[bold]Access:[/bold] {status.access_level.title()}")
        if status.is_public:
            console.print(f"[bold]Public Link:[/bold] {status.public_link}")
        
        if status.collaborators:
            console.print("\n[bold]Collaborators:[/bold]")
            table = Table(show_header=True, header_style="bold")
            table.add_column("Email")
            table.add_column("Role")
            table.add_column("Status")
            
            for c in status.collaborators:
                status_text = "[yellow]Pending[/yellow]" if c.is_pending else "[green]Active[/green]"
                role_color = "blue" if c.role == "owner" else "cyan" if c.role == "editor" else "dim"
                table.add_row(c.email, f"[{role_color}]{c.role}[/{role_color}]", status_text)
            
            console.print(table)
        else:
            console.print("\n[dim]No collaborators[/dim]")
    except NLMError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"\n[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)


@app.command("public")
def share_public(
    notebook: str = typer.Argument(..., help="Notebook ID or alias"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Enable public link access (anyone with link can view)."""
    try:
        notebook_id = get_alias_manager().resolve(notebook)
        with get_client(profile) as client:
            public_link = client.set_public_access(notebook_id, is_public=True)
        
        console.print("[green]✓[/green] Public access enabled")
        console.print(f"[bold]Link:[/bold] {public_link}")
    except NLMError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"\n[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)


@app.command("private")
def share_private(
    notebook: str = typer.Argument(..., help="Notebook ID or alias"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Disable public link access (restricted to collaborators only)."""
    try:
        notebook_id = get_alias_manager().resolve(notebook)
        with get_client(profile) as client:
            client.set_public_access(notebook_id, is_public=False)
        
        console.print("[green]✓[/green] Public access disabled")
        console.print("[dim]Notebook is now restricted to collaborators[/dim]")
    except NLMError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"\n[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)


@app.command("invite")
def share_invite(
    notebook: str = typer.Argument(..., help="Notebook ID or alias"),
    email: str = typer.Argument(..., help="Email address to invite"),
    role: str = typer.Option("viewer", "--role", "-r", help="Role: viewer or editor"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Invite a collaborator by email."""
    if role.lower() not in ("viewer", "editor"):
        console.print(f"[red]Error:[/red] Invalid role '{role}'. Must be 'viewer' or 'editor'.")
        raise typer.Exit(1)
    
    try:
        notebook_id = get_alias_manager().resolve(notebook)
        with get_client(profile) as client:
            result = client.add_collaborator(notebook_id, email, role=role.lower())
        
        if result:
            console.print(f"[green]✓[/green] Invited {email} as {role.lower()}")
        else:
            console.print(f"[yellow]⚠[/yellow] Invitation may have failed")
    except NLMError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.hint:
            console.print(f"\n[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)
