from rich.console import Console
from rich.table import Table
from rich.progress import track
import time

console = Console()

def display_rich_elements():
    """
    Demonstrate rich terminal UI patterns.
    """
    # Styled output
    console.print("\n[bold green]Success![/] CLI application started.")
    console.print("[bold red]Error![/] Configuration file not found.", style="red")

    # Tables
    table = Table(title="System Component Status")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Uptime", justify="right", style="green")

    table.add_row("Database", "Online", "14d 2h")
    table.add_row("API Gateway", "Online", "2d 5h")
    table.add_row("Worker Node (A)", "[bold yellow]Degraded[/]", "45m")
    
    console.print(table)

    # Progress bars
    items = list(range(100))
    for item in track(items, description="[blue]Initializing components...[/]"):
        # Simulate work
        time.sleep(0.01)

if __name__ == "__main__":
    display_rich_elements()
