import sys
import functools
import click
from typing import Optional, Callable

def safe_execution(func: Callable):
    """
    Decorator for robust CLI command execution with standard error handling.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Optional[int]:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            click.secho(f"Error: File not found - {e}", fg="red", err=True)
            sys.exit(1)
        except ValueError as e:
            click.secho(f"Error: Invalid input - {e}", fg="red", err=True)
            sys.exit(1)
        except click.ClickException as e:
            # Click's own exceptions are handled by Click, but can be caught here if needed
            raise e
        except Exception as e:
            click.secho(f"Internal System Error: {e}", fg="red", bold=True, err=True)
            sys.exit(1)
    return wrapper

@click.command()
@click.argument('path', type=click.Path())
@safe_execution
def read_file(path: str) -> None:
    """Read a file safely."""
    with open(path, 'r') as f:
        print(f.read())

if __name__ == '__main__':
    read_file()
