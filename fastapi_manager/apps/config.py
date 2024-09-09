import inspect
from types import ModuleType
from pathlib import Path
from importlib import import_module

from starlette.routing import Router

from fastapi_manager.utils.module_loading import import_string, module_has_submodule

MODELS_MODULE_NAME = "models"
APPS_MODULE_NAME = "config"
ROUTER_MODULE_NAME = "router"


class AppCreator:
    def __init__(self):
        self.app_module: ModuleType = None
        self.app_config: type[AppConfig] = None
        self.app_name: str = None

    def try_get_module(self):
        try:
            self.app_module = import_module(self.app_entry)
        except:
            pass

    def try_get_config_or_init_new(self):
        if module_has_submodule(self.app_module, APPS_MODULE_NAME):
            mod = import_module(f"{self.app_entry}.{APPS_MODULE_NAME}")
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                if issubclass(obj, AppConfig) and name != "AppConfig":
                    self.app_config = obj
                    break
        if self.app_config is None:
            self.app_config = AppConfig
            self.app_name = self.app_entry

    def try_import_as_string(self):
        if self.app_config is None:
            try:
                self.app_config = import_string(self.app_entry)
            except ImportError:
                pass

    def try_set_appconfig_name(self):
        if self.app_name is None:
            try:
                self.app_name = self.app_config.name
            except AttributeError:
                raise Exception(f"{self.app_entry} class must suply name attribute")

    def try_import_module_by_config_name(self):
        try:
            self.app_module = import_module(self.app_name)
        except ImportError:
            raise Exception(
                "Cannot import '%s'. Check that '%s.%s.name' is correct."
                % (
                    self.app_name,
                    self.app_config.__module__,
                    self.app_config.__qualname__,
                )
            )

    def create(self, app_entry):
        self.app_entry = app_entry
        self.try_get_module()
        self.try_get_config_or_init_new()
        self.try_import_as_string()

        if self.app_module is None and self.app_config is None:
            raise Exception(
                "Error importing or configuring app '%s'. "
                "Is it installed?" % self.app_entry
            )

        self.try_set_appconfig_name()

        self.try_import_module_by_config_name()
        return self.app_config(self.app_name, self.app_module)

    @staticmethod
    def get_unique_module_path(module):
        paths = list(getattr(module, "__path__", []))
        if len(paths) != 1:
            filename = getattr(module, "__file__", None)
            if filename is not None:
                paths = [Path(filename).parent]
            else:
                # For unknown reasons, sometimes the list returned by __path__
                # contains duplicates that must be removed (#25246).
                paths = list(set(paths))
        if len(paths) > 1:
            raise Exception(
                "The app module %r has multiple filesystem locations (%r); "
                "you must configure this app with an AppConfig subclass "
                "with a 'path' class attribute." % (module, paths)
            )
        elif not paths:
            raise Exception(
                "The app module %r has no filesystem location, "
                "you must configure this app with an AppConfig subclass "
                "with a 'path' class attribute." % module
            )
        return paths[0]


class AppConfig:
    def __init__(self, app_name: str, app_module: ModuleType):
        # full doted path
        self.name = app_name

        # module where stored config.py file
        self.module = app_module

        # unique app label
        self.label = app_name.rpartition(".")[2]
        if not self.label.isidentifier():
            raise Exception(
                f"The app label '{self.label}' is not a valid Python identifier."
            )

        # models module
        # module where stored all models for current app
        self.models_module = None

        # list of models class for current app
        self.models = None

        # global apps registry
        self.app_registry = None

        self.path = AppCreator.get_unique_module_path(app_module)

    async def on_ready(self):
        """
        Override this to call when the app is ready
        """
        pass

    @classmethod
    def create(cls, app_entry: str):
        return AppCreator().create(app_entry)

    def import_models(self):
        self.models = self.app_registry.models_dict[self.label]
        if module_has_submodule(self.module, MODELS_MODULE_NAME):
            models_module_name = f"{self.name}.{MODELS_MODULE_NAME}"
            self.models_module = import_module(models_module_name)

    def get_model(self, model_name, require_ready=True):
        if require_ready:
            self.app_registry.check_models_ready()
        else:
            self.app_registry.check_apps_ready()
        try:
            return self.models[model_name.lower()]
        except KeyError:
            raise LookupError(
                "App '%s' doesn't have a '%s' model." % (self.label, model_name)
            )

    def get_models(self, include_auto_created=False, include_swapped=False):
        self.app_registry.check_models_ready()
        for model in self.models.values():
            # TODO: remove django args
            # if model._meta.auto_created and not include_auto_created:
            #     continue
            # if model._meta.swapped and not include_swapped:
            #     continue
            yield model

    def get_router(self, endpoint_var):
        if module_has_submodule(self.module, ROUTER_MODULE_NAME):
            mod = import_module(f"{self.name}.{ROUTER_MODULE_NAME}")
            for name, obj in inspect.getmembers(mod):
                if name == endpoint_var:
                    return obj
        return []

    def __str__(self):
        return "<%s: %s> in (%s)" % (
            self.__class__.__name__,
            self.label,
            Path(self.__module__.rpartition(".")[2]).absolute(),
        )
