from .run_server import cli as server_typer
from .template_creation import cli as file_typer

# list of commands typer instances
COMMANDS = [server_typer, file_typer]

__all__ = ["COMMANDS"]
