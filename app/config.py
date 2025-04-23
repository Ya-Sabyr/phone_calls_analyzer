import logging
import os
import sys

from celery import Celery
from dotenv import load_dotenv
# from logtail import LogtailHandler

load_dotenv()

class BackendConfig():
    ALLOWED_HOSTS: list[str] = os.getenv("ALLOWED_HOSTS", "*").split(",")
    DEBUG: bool = os.getenv("DEBUG_MODE", "False") == "False"
    # LOGTAIL_SOURCE_TOKEN: str = os.getenv("LOGTAIL_SOURCE_TOKEN")

    def configure_logging(self):
        # handler = LogtailHandler(source_token=self.LOGTAIL_SOURCE_TOKEN)
        logger = logging.getLogger()  # Get the root logger to apply globally
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        if self.DEBUG:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        # logger.handlers = []  # Clear existing handlers
        # logger.addHandler(handler)
        # logger.addHandler(logging.StreamHandler(sys.stdout))

class CeleryConfig:
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND")
    
    def create_celery_app(self) -> Celery:
        logging.info('Creating celery app...')
        celery_app = Celery(
            'tasks',
            broker=self.CELERY_BROKER_URL,
            backend=self.CELERY_RESULT_BACKEND,
            include=[
                'app.scheduler.tasks',
                ]
        )
        celery_app.conf.update(
            broker_url=self.CELERY_BROKER_URL,
            result_backend=self.CELERY_RESULT_BACKEND,
        )
        return celery_app

celery_config = CeleryConfig()
backend_config = BackendConfig()
