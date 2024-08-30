from .base import File, Folder
from .contents import MANAGE_PY_CONTENT, MODELS_CONTENT

def get_project_folder(project_name):

    root = Folder(project_name)
    root.append(File("manage.py", MANAGE_PY_CONTENT).set_replacer({"{{project_name}}": project_name}))

    subfolder = Folder(project_name)
    subfolder.append(File("settings.toml"))
    subfolder.append(File("main_router.py"))
    subfolder.append(File("asgi.py"))
    subfolder.append(File("__init__.py"))

    root.append(subfolder)
    return root


