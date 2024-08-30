import json
from pathlib import Path
import pytest
from fastapi_manager.core.templates.base import File, Folder, Generator, PathNotExistsError, PathNotEmptyError

@pytest.fixture
def dummy_file():
    return File("test_file.py")


def test_folder():
    folder = Folder("test_folder")
    test_dict = {
        "name": "test_folder",
        "contents": [],
        "path": str(Path("test_folder")),
    }
    assert folder.to_dict() == test_dict
    assert json.loads(folder.to_json()) == test_dict

def test_file(dummy_file):
    test_dict = {
        "name": "test_file.py",
        "content": '',
        "path": str(Path("test_file.py")),
    }
    assert dummy_file.to_dict() == test_dict

def test_file_format(dummy_file):
    test_content = """
        class {{app_name}}Config(AppConfig):
            pass
    """

    dummy_file.set_content(test_content)
    dummy_file.set_replacer({"{{app_name}}": "TestApp"})
    new_content = dummy_file.format()
    assert new_content == test_content.replace("{{app_name}}", "TestApp")



def test_is_empty(tmpdir):
    # Create an empty directory
    empty_dir = tmpdir.mkdir("empty_dir")
    assert Generator.is_empty(Path(empty_dir)) == True

    # Create a non-empty directory
    non_empty_dir = tmpdir.mkdir("non_empty_dir")
    non_empty_dir.join("file.txt").write("content")
    assert Generator.is_empty(Path(non_empty_dir)) == False

# Test generate_structure method with an empty base path
def test_generate_structure_empty_base_path(tmpdir):
    json_structure = """
    {
      "name": "root",
      "path": "root",
      "contents": [
        {
          "name": "script1.py",
          "size": 20,
          "content": "print('Hello, World!')",
          "path": "root/script1.py"
        }
      ]
    }
    """
    base_path = tmpdir.mkdir("output_dir")

    # Act & Assert
    with pytest.raises(PathNotEmptyError):
        base_path.join("existing_file.txt").write("already exists")
        Generator.generate_structure(json_structure, base_path=str(base_path))

# Test generate_structure method with a valid structure and empty base path
def test_generate_structure_valid(tmpdir):
    json_structure = """
    {
      "name": "root",
      "path": "root",
      "contents": [
        {
          "name": "script1.py",
          "size": 20,
          "content": "print('Hello, World!')",
          "path": "root/script1.py"
        },
        {
          "name": "subfolder",
          "path": "root/subfolder",
          "contents": [
            {
              "name": "script2.py",
              "size": 39,
              "content": "def add(a, b):\\n    return a + b",
              "path": "root/subfolder/script2.py"
            }
          ]
        }
      ]
    }
    """
    base_path = tmpdir.mkdir("output_dir")

    # Assert the directory is empty
    assert Generator.is_empty(Path(base_path)) == True

    # Act
    Generator.generate_structure(json_structure, base_path=str(base_path))

    # Assert
    root_path = Path(base_path)
    assert root_path.exists() and root_path.is_dir()

    script1_path = root_path / "script1.py"
    assert script1_path.exists() and script1_path.is_file()
    assert script1_path.read_text() == "print('Hello, World!')"

    subfolder_path = root_path / "subfolder"
    assert subfolder_path.exists() and subfolder_path.is_dir()

    script2_path = subfolder_path / "script2.py"
    assert script2_path.exists() and script2_path.is_file()
    assert script2_path.read_text() == "def add(a, b):\n    return a + b"

# Test generate_structure method with base_path as None
def test_generate_structure_no_base_path(tmpdir):
    json_structure = """
    {
      "name": "root",
      "path": "root",
      "contents": [
        {
          "name": "script1.py",
          "size": 20,
          "content": "print('Hello, World!')",
          "path": "root/script1.py"
        }
      ]
    }
    """

    # Act
    Generator.generate_structure(json_structure, base_path=None)

    # Assert
    root_path = Path("root").resolve()
    assert root_path.exists() and root_path.is_dir()

    script1_path = root_path / "script1.py"
    assert script1_path.exists() and script1_path.is_file()
    assert script1_path.read_text() == "print('Hello, World!')"

    # Clean up
    if root_path.exists():
        for item in root_path.glob("**/*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
        root_path.rmdir()

# Test the error handling for a non-existent path
def test_generate_structure_nonexistent_path(tmpdir):
    json_structure = """
    {
      "name": "root",
      "path": "root",
      "contents": []
    }
    """
    # Act & Assert
    with pytest.raises(PathNotExistsError):
        Generator.generate_structure(json_structure, base_path="nonexistent_path")
