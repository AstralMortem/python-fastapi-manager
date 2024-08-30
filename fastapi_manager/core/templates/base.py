import json
from mailbox import NotEmptyError
from pathlib import Path
from tabnanny import check
from typing import Union, Optional, List

from pydantic.v1 import PathNotExistsError


class File:
    def __init__(self, name: str, content: str = ""):
        self._name = name
        self._content = content
        self.replacer = {}


    @property
    def name(self):
        return self._name

    @property
    def content(self):
        return self._content

    def set_content(self, new_content):
        self._content = new_content

    def append_content(self, new_content):
        self._content += new_content

    def extend_replacer(self, replacer: dict[str, str]):
        self.replacer.update(replacer)

    def set_replacer(self, replacer: dict):
        self.replacer = replacer

    def format(self):
        if self.replacer:
            for placeholder, val in self.replacer.items():
                if placeholder in self.content:
                    self._content = self._content.replace(placeholder, val)
        return self._content

    def __str__(self) -> str:
        return f"  |-> {self._name}"

    def to_dict(self, parent_path: Union[str,Path] = "") -> dict:
        path = Path(parent_path).joinpath(self._name)
        return {
            "name": self._name,
            "content": self._content,
            "path": str(path),
        }


class Folder(list):
    def __init__(self, name: str):
        super().__init__()
        self._name = name

    @property
    def name(self):
        return self._name

    def append(self, item: Union[File, "Folder"]):
        if not isinstance(item, (File, Folder)):
            raise TypeError("Only File or Folder objects can be added")
        if isinstance(item, File) and any(f.name == item.name for f in self if isinstance(f, File)):
            raise ValueError(f"File with name '{item.name}' already exists in folder '{self._name}'.")
        if isinstance(item, Folder) and any(f.name == item.name for f in self if isinstance(f, Folder)):
            raise ValueError(f"Folder with name '{item.name}' already exists in folder '{self._name}'.")
        super().append(item)

    def extend(self, items: list[Union[File, "Folder"]]):
        for item in items:
            self.append(item)

    def __str__(self, level=0) -> str:
        indent = " " * (level * 2)
        result = f"{indent}|-> {self._name}\n"
        for item in self:
            result += f"{indent}{item}\n" if isinstance(item, File) else item.__str__(level + 1)
        return result

    def to_dict(self, parent_path: Union[str,Path] = "") -> dict:
        path = Path(parent_path).joinpath(self._name)
        result = {"name": self._name, "path": str(path), "contents": []  }
        for item in self:
            if isinstance(item, File):
                result["contents"].append(item.to_dict(path))
            elif isinstance(item, Folder):
                result["contents"].append(item.to_dict(path))
        return result

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

# class Generator:
#
#     @staticmethod
#     def create_file(file:dict, current_path: Union[str, Path]):
#         new_path = Path(current_path).joinpath(file["name"]).absolute()
#         with open(new_path, "w", encoding="utf8") as f:
#             f.write(file.get("content", ""))
#             f.close()
#
#     @staticmethod
#     def create_folder(folder:dict, current_path: Union[str, Path]):
#         new_path = Path(current_path).joinpath(folder["name"]).absolute()
#         if folder.get("create") and new_path.exists():
#             raise ValueError(f"Folder with name '{folder.get('name')}' already exists")
#         if not folder.get("create") and not new_path.exists():
#             raise ValueError(f"Folder with name '{folder.get('name')}' does not exist")
#         new_path.mkdir(exist_ok=folder.get("create"))
#         return new_path
#
#     @classmethod
#     def _walk_structure(cls, structure: dict, current_path: Union[str, Path]):
#         # Ensure the current directory exists
#         current_path = cls.create_folder(structure, current_path)
#
#
#         # Iterate over the contents of the current folder
#         for item in structure.get("contents", []):
#             if "contents" in item:
#                 # It's a folder
#                 new_path = cls.create_folder(item, current_path)
#                 cls._walk_structure(item, new_path)
#             else:
#                 # It's a file
#                 cls.create_file(item, current_path)
#
#     @classmethod
#     def write_structure(cls, structure: Union[dict, str], root_dir: Union[str, Path]):
#         if isinstance(structure, str):
#             structure = json.loads(structure)
#         cls._walk_structure(structure, root_dir)

class PathNotExistsError(Exception):
    pass

class PathNotEmptyError(Exception):
    pass

class Generator:

    @staticmethod
    def is_empty(path: Path):
        return len(list(path.iterdir())) == 0

    @staticmethod
    def generate_structure(struct: str, base_path: Union[str, Path, None] = None):
        structure = json.loads(struct)


        if base_path is not None:
            # check if path exists and empty
            path = Path(base_path).resolve()
            if not path.exists():
                raise PathNotExistsError(f"{base_path} does not exist.")
            if not Generator.is_empty(path):
                raise PathNotEmptyError(f"{base_path} is not empty")
        else:
            # if base_path none, create root folder from struct path
            path = Path(structure["path"]).resolve()


        Generator._walk_structure(structure, path)

    @staticmethod
    def _walk_structure(structure: dict, current_path: Path):
        current_path.mkdir(exist_ok=True)
        for item in structure.get("contents", []):
            if "contents" in item:  # It's a folder
                folder_path = current_path.joinpath(item["name"])
                folder_path.mkdir(exist_ok=True)
                Generator._walk_structure(item, folder_path)
            else:  # It's a file
                file_path = current_path.joinpath(item["name"])
                with open(file_path, "w") as f:
                    f.write(item.get("content", ""))
                    f.close()


if __name__ == '__main__':
    project = "test_project"
    root = Folder(project)
    subfolder = Folder(project)
    subfolder.extend([
        File("settings.toml"),
        File("__init__.py"),
        File("main_router.py"),
        File("asgi.py"),
    ])
    root.extend([File("manage.py"), subfolder])
    print(root.to_json())
    Generator.generate_structure(root.to_json())

