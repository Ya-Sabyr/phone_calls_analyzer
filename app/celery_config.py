from app.config import celery_config

celery_app = celery_config.create_celery_app()

import app.scheduler.config