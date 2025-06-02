from app.celery_config import celery_app
from app.crms.bitrix import BitrixCallRecorder
from app.stt.stt import process_recordings
from app.openai.utils import run_recommendations
import logging

@celery_app.task
def process_call_task():
    webhook = ""
    recorder = BitrixCallRecorder(webhook)
    call_details = recorder.process_call_records_btx()
    logging.debug(call_details)
    if not call_details:   
        return
    process_recordings()
    run_recommendations(call_details)


# @celery_app.task
# def process_call_records_btx_task():
#     webhook = "https://businessautomation.bitrix24.kz/rest/4026/cvw8q51bm4sv4qf1"
#     recorder = BitrixCallRecorder(webhook)
#     asyncio.run(recorder.process_call_records_btx())

# @celery_app.task
# def process_recordings_task():
#     asyncio.run(process_recordings())
