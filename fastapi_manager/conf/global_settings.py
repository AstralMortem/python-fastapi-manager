# Global Debug state default False
DEBUG = False

# FastAPI Meta
PROJECT_TITLE = "FastAPI"
PROJECT_VERSION = "1.0.0"

# Use to set app behind proxy, if for exm. Traefic request on /api/v1/test, we set PROJECT_ROOT_PATH
# as /api/v1, in routes we set /test. see more https://fastapi.tiangolo.com/advanced/behind-a-proxy/
PROJECT_ROOT_PATH = ""

# applications to populate in registry
INSTALLED_APPS = []

# database dict
DATABASES = {
    "default": {
        "engine": "tortoise.backends.asyncpg",
        "credentials": {
            "host": "localhost",
            "port": "5432",
            "user": "postgres",
            "password": "postgres",
            "database": "test",
        },
    },
}


TIMEZONE = "UTC"
