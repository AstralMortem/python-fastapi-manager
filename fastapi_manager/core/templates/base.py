import json
from pathlib import Path
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
        return self

    def append_content(self, new_content):
        self._content += new_content
        return self

    def extend_replacer(self, replacer: dict[str, str]):
        self.replacer.update(replacer)
        return self

    def set_replacer(self, replacer: dict):
        self.replacer = replacer
        return self

    def format_content(self):
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
            "content": self.format_content(),
            "path": str(path),
        }


class Folder(list):
    def __init__(self, name: str):
        super().__init__()
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

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

class PathNotExistsError(Exception):
    pass

class PathNotEmptyError(Exception):
    pass

class PathAlreadyExistsError(Exception):
    pass

class Generator:

    @staticmethod
    def is_empty(path: Path):
        return len(list(path.iterdir())) == 0



    @staticmethod
    def generate_structure(struct: str, base_path: Union[str, Path, None] = None, create_root = False):
        structure = json.loads(struct)

        if base_path is None:
            path = Path(structure["path"]).resolve()
            if path.exists():
                raise PathAlreadyExistsError(f"{path} already exists.")
        else:
            path = Path(base_path).resolve()
            if create_root:
                path = path.joinpath(structure["path"]).resolve()
                if path.exists():
                    raise PathAlreadyExistsError(f"{path} already exists.")
            else:
                if not path.exists():
                    raise PathNotExistsError(f"{base_path} does not exist.")
                if not Generator.is_empty(path):
                    raise PathNotEmptyError(f"{base_path} is not empty")

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


