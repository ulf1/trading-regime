# /// script
# dependencies = ["httpx", "rich"]
# ///
import httpx
from rich import print

def main():
    """Example script with inline PEP 723 metadata for 'uv' usage."""
    resp = httpx.get("https://api.github.com/zen")
    print(f"[bold blue]GitHub Zen:[/bold blue] {resp.text}")

if __name__ == "__main__":
    main()
