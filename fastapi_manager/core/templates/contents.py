# -------------- SERVER CONTENT --------------------------------

MANAGE_PY_CONTENT = """#!/usr/bin/env python
import os

def main():
    os.environ.setdefault("FASTAPI_SETTINGS", "{{project_name}}.settings")
    try:
        from fastapi_manager.core.cli import cli
    except ImportError as exc:
        raise ImportError("Could not import fastapi_manager. Are you sure you installed it?") from exc
    
    cli()
    
if __name__ == '__main__':
    main()
"""

ASGI_CONTENT = """# ASGI config for {{project_name}} project.
# It exposes the ASGI callable as a module-level variable named application

import os
os.environ.setdefault("FASTAPI_SETTINGS", "{{project_name}}.settings")


from fastapi_manager.core.asgi import Application
application = Application()

"""

SETTINGS_TOML_CONTENT = """[default]
DEBUG = true
INSTALLED_APPS = []
ROOT_ROUTER = "{{project_name}}.router"
"""

# -------------- APP CONTENT --------------------------------

MODELS_CONTENT = "from fastapi_manager.db import models, fields"

APP_CONFIG_CONTENT = """from fastapi_manager.apps import AppConfig

class {{camel_case_app_name}}Config(AppConfig):
    name = "{{app_name}}"
"""

ROUTER_CONTENT = """from fastapi_manager.router import path

ENDPOINTS = []"""

SERVICES_CONTENT = """from fastapi_manager.services import BaseService

"""

VIEWS_CONTENT = """from fastapi_manager.viewsets import ModelViewSet"""
