from pathlib import Path
import os
from fastapi_manager.core.templates import Generator, get_project_folder, get_app_folder
from fastapi_manager.core.cli.typer import AsyncTyper

cli = AsyncTyper()


@cli.command()
def startproject(project_name: str, project_path: str = None, settings: str = None):
    if settings is not None:
        os.environ.setdefault("FASTAPI_SETTINGS", settings)

    struct = get_project_folder(project_name)
    try:
        Generator.generate_structure(struct.to_json(), project_path)
    except Exception as e:
        print(f"[red]{e}[/red]")


@cli.command()
def startapp(app_name: str, project_path: str = None, settings: str = None):
    from fastapi_manager.conf import settings as conf

    if settings is not None:
        os.environ.setdefault("FASTAPI_SETTINGS", settings)

    struct = get_app_folder(app_name)
    try:
        if project_path is None:
            project_path = Path(conf.BASE_DIR)
        Generator.generate_structure(struct.to_json(), project_path, True)
    except Exception as e:
        print(f"[red]{e}[/red]")
