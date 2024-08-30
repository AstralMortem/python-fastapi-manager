from .base import BaseCommand
from fastapi_manager.core.templates import Generator, get_project_folder

class CreateProject(BaseCommand):
    name = "startproject"

    @classmethod
    def execute(cls, project_name: str, project_path:str = None, settings: str = None):
        project_structure = get_project_folder(project_name)
        try:
            Generator.generate_structure(project_structure.to_json(), project_path)
        except Exception as e:
            print(e)

class Test(BaseCommand):
    name = "test"
