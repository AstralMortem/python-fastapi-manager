import typer
import inspect
from .commands.base import BaseCommand
from fastapi_manager import setup


def get_all_command():
    from fastapi_manager.core.cli import commands

    for name, obj in inspect.getmembers(commands, inspect.isclass):
        if issubclass(obj, BaseCommand):
            yield obj


cli = typer.Typer()

for command in get_all_command():
    handler = typer.models.CommandInfo(name=command.name, callback=command.execute)
    cli.registered_commands.append(handler)
else:
    # setup()
    pass
