from fastapi_manager.core.cli.commands.base import BaseCommand
from fastapi_manager.core.cli.typer import get_all_command
import pytest
from unittest.mock import patch, Mock
import typer

@pytest.fixture()
def command():
    class TestCommand(BaseCommand):
        name = "test_command"

        @classmethod
        def execute(cls, name, age):
            pass
    return TestCommand


def test_cli_base_commands_name(command):
    assert command.name == "test_command"

def test_get_command_func(command):
    with patch("fastapi_manager.core.cli.commands", new=Mock()) as mock_commands:
        mock_commands.__dict__.update({"TestCommand": command})

        new_commands = list(get_all_command())
        assert len(new_commands) == 1
        assert new_commands[0].name == "test_command"
        assert new_commands[0] is command

# def test_typer_handler(command):
#     cli = typer.Typer()
#     with patch("fastapi_manager.core.cli.commands", new=Mock()) as mock_commands:
#         mock_commands.__dict__.update({"TestCommand": command})
#
#         for command in get_all_command():
#             handler = typer.models.CommandInfo(
#                 name=command.name,
#                 callback=command.execute
#             )
#             cli.registered_commands.append(handler)
#
