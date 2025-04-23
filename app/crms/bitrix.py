import logging
import os
import requests
import pytz

from datetime import datetime, timedelta
from fast_bitrix24 import Bitrix

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the recordings directory
RECORDINGS_DIR = os.path.join('app', 'recordings')

class BitrixCallRecorder:
    def __init__(self, webhook_url: str, timezone_str: str = 'Asia/Almaty'):
        self.bx = Bitrix(webhook_url)
        self.timezone = pytz.timezone(timezone_str)

        os.makedirs(RECORDINGS_DIR, exist_ok=True)

    def fetch_call_data(self):
        """Fetches call data from Bitrix24 for the last 5 minutes."""
        try:
            now = datetime.now(self.timezone)
            five_minutes_ago = now - timedelta(minutes=5)

            now_str = now.isoformat()
            five_minutes_ago_str = five_minutes_ago.isoformat()

            logger.debug(f"Fetching calls from {five_minutes_ago_str} to {now_str}")

            # Fetch call data using the time range for the last 5 minutes
            call_data = self.bx.get_all('voximplant.statistic.get', params={
                "FILTER": {
                    ">=CALL_START_DATE": five_minutes_ago_str,
                    "<CALL_START_DATE": now_str,
                }
            })

            logger.info(f"Fetched {len(call_data)} call records.")
            return call_data
        except Exception as e:
            logger.error(f"Failed to fetch call data: {e}")
            return []

    def download_call_record(self, record_url: str):
        """Загружает запись разговора с указанного URL."""
        try:
            response = requests.get(record_url)
            response.raise_for_status()  # Check for HTTP errors
            logger.info(f"Successfully downloaded call record from {record_url}.")
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download the call record from {record_url}: {e}")
            return None

    def save_call_record(self, record_content: bytes, file_name: str):
        """Сохраняет загруженную запись разговора в указанный путь к файлу."""
        file_path = os.path.join(RECORDINGS_DIR, file_name)
        try:
            with open(file_path, "wb") as file:
                file.write(record_content)
            logger.info(f"Call record saved successfully at {file_path}.")
        except Exception as e:
            logger.error(f"Failed to save call record: {e}")

    def get_manager(self, manager_id: str):
        """pass"""
        manager = self.bx.get_by_ID('im.user.get', [manager_id])
        logging.info(manager['name'])
        return manager['name']
        

    def process_call_records_btx(self):
        """Основной метод обработки и сохранения записей звонков."""
        call_data = self.fetch_call_data()

        if not call_data:
            logger.warning("No call records found.")
            return False

        call_details = []

        for call in call_data:
            record_url = call.get('CALL_RECORD_URL')
            manager = self.get_manager(call.get('PORTAL_USER_ID'))
            call_duration = call.get('CALL_DURATION')
            call_details.append({
                "manager": manager,
                "call_duration": call_duration
            })
            

            if record_url:
                call_record_content = self.download_call_record(record_url)

                if call_record_content:
                    # Save the file in the RECORDINGS_DIR with a unique name
                    file_name = f"call_record_{call['CALL_ID']}.mp3"
                    self.save_call_record(call_record_content, file_name)
                else:
                    logger.warning(f"No content available for call record {call['CALL_ID']}.")
            else:
                logger.warning(f"No record URL found for call {call['CALL_ID']}.")
        
        return call_details



# Функция получения истории звонков
# Документация Б24: https://dev.1c-bitrix.ru/rest_help/scope_telephony/voximplant/statistic/voximplant_statistic_get.php
# [ Получаем список с детализацией звонков
#     {'ID': '376043',   Идентификатор звонка (для внутренних целей)
#      'PORTAL_USER_ID': '31',   Идентификатор ответившего/позвонившего оператора
#      'PORTAL_NUMBER': '+7342206',
#      'PHONE_NUMBER': '+7999',   Номер клиента
#      'CALL_ID': 'externalCall.***',   Идентификатор звонка
#      'EXTERNAL_CALL_ID': 'FE29***',
#      'CALL_CATEGORY': 'external',
#      'CALL_DURATION': '533',   Длительность звонка в секундах
#      'CALL_START_DATE': '2024-06-26T09:47:15+05:00',   Время инициализации звонка
#      'CALL_RECORD_URL': 'https://vpbx034215957.domru.biz/api/v2/call-records/record/***/',
#      'CALL_VOTE': '0',   Оценка звонка
#      'COST': '0.0000',
#      'COST_CURRENCY': '',
#      'CALL_FAILED_CODE': '200',   Код вызова (справочник кодов: https://dev.1c-bitrix.ru/rest_help/scope_telephony/codes_and_types.php#call_failed_code)
#      'CALL_FAILED_REASON': '',   Текстовое описание кода вызова
#      'CRM_ENTITY_TYPE': 'CONTACT',   Тип объекта CRM, к которому прикреплено дело
#      'CRM_ENTITY_ID': '225059',   Идентификатор объекта CRM
#      'CRM_ACTIVITY_ID': '584661',   Идентификатор дела CRM
#      'REST_APP_ID': '4',   Идентификатор приложения интеграции внешней телефонии
#      'REST_APP_NAME': 'Облачная АТС Дом.ру Бизнес',
#      'TRANSCRIPT_ID': None,   Идентификатор расшифровки звонка
#      'TRANSCRIPT_PENDING': 'N',   Y\N. Признак того, что расшифровка будет получена позднее
#      'SESSION_ID': None,      Идентификатор сессии звонка на стороне Voximplant
#      'REDIAL_ATTEMPT': None,   Номер попытки дозвониться (для обратных звонков)
#      'COMMENT': None,   Комментарий к звонку
#      'RECORD_DURATION': None,
#      'RECORD_FILE_ID': 495911,   Идентификатор файла с записью звонка
#      'CALL_TYPE': '2'   Тип вызова (справочник кодов: https://dev.1c-bitrix.ru/rest_help/scope_telephony/codes_and_types.php#call_failed_code
#      },
