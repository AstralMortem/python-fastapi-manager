from .base import File, Folder
from .contents import *
from fastapi_manager.utils.string import convert_to_camel_case


def get_app_folder(app_name, **kwargs):
    root = Folder(app_name)
    root.append(
        File("config.py", APP_CONFIG_CONTENT).set_replacer(
            {
                "camel_case_app_name": convert_to_camel_case(app_name, True),
                "app_name": app_name,
            }
        )
    )
    root.append(File("__init__.py"))
    root.append(File("models.py", MODELS_CONTENT))
    root.append(File("router.py", ROUTER_CONTENT))
    root.append(File("_views.py"))
    root.append(File("services.py"))

    return root


def get_project_folder(project_name, **kwargs):

    # Root Folder
    root = Folder(project_name)

    manage_py = File("manage.py", MANAGE_PY_CONTENT)
    manage_py.set_replacer({"project_name": project_name})

    root.append(manage_py)

    # Project folder
    subfolder = Folder(project_name)

    settings_toml = File("settings.toml", SETTINGS_TOML_CONTENT)
    settings_toml.set_replacer({"project_name": project_name})

    router_py = File("router.py", ROUTER_CONTENT)

    asgi_py = File("asgi.py", ASGI_CONTENT)
    asgi_py.set_replacer({"project_name": project_name})

    subfolder.extend([settings_toml, router_py, asgi_py, File("__init__.py")])

    root.append(subfolder)
