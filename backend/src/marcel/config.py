import os
from logging.config import dictConfig
from pathlib import Path

DATA_ROOT = Path(os.environ.get("DATA_ROOT", ""))
DATA_PATH = DATA_ROOT / os.environ.get("DATA_PATH", "")
FAQ_PATH = DATA_ROOT / os.environ.get("FAQ_PATH", "")
ADMINS_PATH = DATA_ROOT / os.environ.get("ADMINS_PATH", "")

LLM_BASE_URL = os.environ.get("LLM_BASE_URL")
LLM_API_KEY = os.environ.get("LLM_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME")

SECRET_KEY = os.environ["SECRET_KEY"]
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])

DATABASE_URI = os.environ.get("DATABASE_URI")


def setup_logging():
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(processName)s: %(process)d] [%(levelname)s] %(name)s: %(message)s"
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "uvicorn_access": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "uvicorn_error": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["uvicorn_error"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["uvicorn_access"],
                "level": "INFO",
                "propagate": False,
            },
            "marcel": {
                "handlers": ["default"],
                "level": "DEBUG",
                "propagate": False,
            },
            "__main__": {
                "handlers": ["default"],
                "level": "DEBUG",
                "propagate": False,
            },
            "": {
                "handlers": ["default"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }
    dictConfig(config)
