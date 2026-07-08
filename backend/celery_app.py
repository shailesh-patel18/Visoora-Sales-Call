import os
from celery import Celery
from security.config import settings

# Initialize Celery
# Defaulting to localhost redis if setting is not provided, for local dev fallback
redis_url = getattr(settings, "redis_url", os.getenv("REDIS_URL", "redis://localhost:6379/0"))

celery_app = Celery(
    "visoora_worker",
    broker=redis_url,
    backend=redis_url,
    include=["ai_platform.tasks", "notifications.tasks"]
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Add exponential backoff configuration for tasks
    task_publish_retry=True,
    task_publish_retry_policy={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    }
)

if __name__ == "__main__":
    celery_app.start()
