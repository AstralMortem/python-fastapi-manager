from .typer import AsyncTyper
from .commands import COMMANDS
from fastapi_manager import setup

cli = AsyncTyper()
cli.add_event_handler("startup", setup)


for command in COMMANDS:
    cli.register_commands(command)

__all__ = ["cli"]
