from io import StringIO
from rich.console import Console
from rich.table import Table

def render_status_table(console: Console):
    table = Table(title="System Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_row("API", "[bold green]Online[/bold green]")
    table.add_row("Database", "[bold red]Offline[/bold red]")
    console.print(table)

def test_rich_output_stripping():
    """Testing Rich output by stripping ANSI codes."""
    # Method A: Use record=True and export_text()
    console = Console(file=StringIO(), record=True, width=80) 
    render_status_table(console)
    
    # export_text() strips all ANSI markup automatically
    plain_text = console.export_text()
    
    assert "System Status" in plain_text
    assert "API" in plain_text
    assert "Online" in plain_text
    assert "Database" in plain_text

def test_rich_output_capture():
    """Testing Rich output using the capture context manager."""
    console = Console()
    with console.capture() as capture:
        console.print("Status: [green]OK[/green]")
    
    captured_output = capture.get()
    # Note: captured_output might still contain ANSI if not handled. 
    # Usually console.capture() is used when you want the RAW output including codes,
    # or you configure the console to NOT emit codes.
    assert "Status: OK" in captured_output
