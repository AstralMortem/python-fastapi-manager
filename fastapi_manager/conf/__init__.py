from typing import Union

import dynaconf
from pathlib import Path
from fastapi_manager.conf import global_settings
import os

GLOBAL_SETTINGS_PATH = Path(global_settings.__file__).absolute()
SETTINGS_ENV = "SETTINGS_MODULE"

# add parsers to convert string to pathlib in configs
dynaconf.utils.parse_conf.converters["@path"] = lambda x: Path(x).absolute()

settings = dynaconf.Dynaconf(
    environments=True,
    load_dotenv=True,
    settings_files=[
        str(GLOBAL_SETTINGS_PATH),
        str(os.environ.get(SETTINGS_ENV, None)),
    ],
    merge_enabled=True,
    envvar_prefix="FASTAPI",
)
