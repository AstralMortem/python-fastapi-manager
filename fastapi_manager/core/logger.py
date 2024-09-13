import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from fastapi_manager.conf import settings

PROJECT_NAME = settings.BASE_DIR.name

# Logger Configuration
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.ERROR,  # Set log level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=(
        [
            logging.StreamHandler(),  # Log to the console
        ]
        + [logging.FileHandler(f"{PROJECT_NAME}.log")]
        if settings.DEBUG
        else []
    ),
)

logger = logging.getLogger(f"{PROJECT_NAME}_fastapi_manager")


# Custom Middleware to log requests
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()

        # Log request details
        logger.info(f"Incoming request: {request.method} {request.url}")

        response = await call_next(request)

        process_time = (datetime.utcnow() - start_time).total_seconds()
        # Log response details
        logger.info(
            f"Response status: {response.status_code} (Processed in {process_time}s)"
        )

        return response


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error occurred: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@asynccontextmanager
async def init_loger(app: FastAPI):

    app.add_exception_handler(Exception, generic_exception_handler)
    yield
