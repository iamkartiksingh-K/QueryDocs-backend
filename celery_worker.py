from celery import Celery
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")


celery_app = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.autodiscover_tasks(["app.services"])

celery_app.conf.task_routes = {
    "app.services.tasks.*": {"queue": "celery"},
}

celery_app.conf.broker_connection_retry_on_startup = True
