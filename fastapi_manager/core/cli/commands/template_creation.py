from pathlib import Path

from .base import BaseCommand
from fastapi_manager.core.templates import Generator, get_project_folder, get_app_folder
from fastapi_manager.conf import settings as settings_file

class CreateProject(BaseCommand):
    name = "startproject"

    @classmethod
    def execute(cls, project_name: str, project_path:str = None, settings: str = None):
        project_structure = get_project_folder(project_name)
        try:
            Generator.generate_structure(project_structure.to_json(), project_path)
        except Exception as e:
            print(e)


class CreateApp(BaseCommand):
    name = "startapp"

    @classmethod
    def execute(cls, app_name: str, project_path: str = None, settings: str = None):
        app_structure = get_app_folder(app_name)
        try:
            if project_path is None:
                project_path = Path(settings_file.BASE_DIR)
            Generator.generate_structure(app_structure.to_json(), project_path, True)
        except Exception as e:
            print(e)