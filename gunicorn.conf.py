"""Config file for gunicorn application."""
import multiprocessing

from loggers import LOGGING_CONFIG
from settings import Settings

bind = f"{Settings.HOST}:{Settings.PORT}"
workers = Settings.WORKERS_COUNT or multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
threads = 1  # default
# reload = True
# reload_engine = "auto"
max_requests = 100  # default 0
max_requests_jitter = 3  # default 0
keepalive = 3  # default 2
timeout = 30  # seconds, default 60
graceful_timeout = 30  # default
logconfig_dict = LOGGING_CONFIG
proc_name = "FastAPI_Back-end"
