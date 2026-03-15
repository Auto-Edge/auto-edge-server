from celery import Celery
from config import settings

app = Celery("autoedge-worker", broker=settings.REDIS_URL, include=['tasks.conversion'])

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=settings.WORKER_CONCURRENCY,
    task_acks_late=True,  # Ensure tasks are not lost if worker crashes
    worker_prefetch_multiplier=1,  # Prevent worker from hogging large ML tasks
)

if __name__ == '__main__':
    app.start()
