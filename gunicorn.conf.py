"""Config file for gunicorn application."""

import multiprocessing

from core.custom_logging import LOGGING_CONFIG

from src.settings import Settings

bind = f"{Settings.SERVER_HOST}:{Settings.SERVER_PORT}"
workers = Settings.SERVER_WORKERS_COUNT or multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
threads = 1  # default
if Settings.APP_DEBUG:
    reload = True
    reload_engine = "auto"
    reload_extra_files = [".env", "settings.py"]
max_requests = 100  # default 0
max_requests_jitter = 3  # default 0
keepalive = 3  # default 2
timeout = 30  # seconds, default 60
graceful_timeout = 30  # default
logconfig_dict = LOGGING_CONFIG
proc_name = "FastAPI_Back-end"
