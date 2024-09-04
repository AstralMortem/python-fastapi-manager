from .base import File, Folder
from .contents import MANAGE_PY_CONTENT, MODELS_CONTENT
from fastapi_manager.utils.string import convert_to_camel_case

def get_project_folder(project_name, **kwargs):


    root = Folder(project_name)
    manage_py = File("manage.py", MANAGE_PY_CONTENT)
    manage_py.set_replacer({"{{project_name}}": project_name})
    root.append(manage_py)


    subfolder = Folder(project_name)
    subfolder.append(File("settings.toml"))
    subfolder.append(File("main_router.py"))
    subfolder.append(File("asgi.py"))
    subfolder.append(File("__init__.py"))
    root.append(subfolder)
    return root


def get_app_folder(app_name, **kwargs):
    root = Folder(app_name)
    root.append(File("config.py").set_replacer({"{{camel_case_app_name}}": convert_to_camel_case(app_name)}))
    root.append(File("__init__.py"))
    root.append(File("models.py"))
    root.append(File("router.py"))
    root.append(File("views.py"))
    root.append(File("services.py"))

    return root

