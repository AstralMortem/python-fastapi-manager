MANAGE_PY_CONTENT = """
#!/usr/bin/env python
from pathlib import Path
import os

def main():
    os.environ.setdefault("FASTAPI_SETTINGS", "./{{project_name}}/settings.toml")
    try:
        from fastapi_manager.core.cli import cli
    except ImportError as exc:
        raise ImportError("Could not import fastapi_manager. Are you sure you installed it?") from exc
    
    cli()
    
if __name__ == '__main__':
    main()
"""

MODELS_CONTENT = "from fastapi_manager.db import models, fields"