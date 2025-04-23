import logging

from app.celery_config import celery_app
from app.scheduler.tasks import process_call_task

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    logging.debug("Setting up periodic tasks...")

    
    sender.add_periodic_task(
        300.0,  # 5 minutes
        process_call_task.s(),  # Task signature
        name="Process call every 5 minutes"
    )
    # Schedule to run `process_call_records_task` every 24 hours
    # sender.add_periodic_task(
    #     86400.0,  # 86400 seconds = 24 hours
    #     process_call_records_btx_task.s(),  # Task signature
    #     name="Process call records every 24 hours"
    # )

    # sender.add_periodic_task(
    #     86400.0,  # 86400 seconds = 24 hours
    #     process_recordings_task.s(),  # Task signature
    #     name="Process recording every 24 hours"
    # )

