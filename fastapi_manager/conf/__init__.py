from typing import Union

import dynaconf
from pathlib import Path
from fastapi_manager.conf import global_settings
from fastapi_manager.utils.module_loading import module_dir
import os
from importlib import import_module

GLOBAL_SETTINGS_PATH = Path(global_settings.__file__).absolute()
SETTINGS_ENV = "FASTAPI_SETTINGS"


def resolve_toml(path: str):
    if path is not None:
        if path.endswith(".toml"):
            path = path.split(".toml")[0]

        module_path, settings_path = path.rsplit(".", 1)
        module_directory = module_dir(import_module(module_path))

        return Path(module_directory).joinpath(settings_path + ".toml").resolve()


# add parsers to convert string to pathlib in configs
dynaconf.utils.parse_conf.converters["@path"] = lambda x: Path(x).absolute()

settings = dynaconf.Dynaconf(
    environments=True,
    load_dotenv=True,
    settings_files=[
        str(GLOBAL_SETTINGS_PATH),
        str(resolve_toml(os.environ.get(SETTINGS_ENV))),
    ],
    merge_enabled=True,
    envvar_prefix="FASTAPI",
)
