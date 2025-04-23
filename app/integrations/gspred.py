import os
import logging
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import gspread

# Define the scope for Google Sheets API
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID')
CREDENTIALS_FILE = "credentials.json"

# Initialize the Google Sheets API client
def get_google_sheet(sheet_id, credentials_file):
    """
    Initializes and returns the Google Sheets client for the given sheet ID.
    
    Args:
        sheet_id (str): The ID of the Google Sheet.
        credentials_file (str): Path to the service account credentials file.

    Returns:
        gspread.models.Spreadsheet: Google Sheet client.
    """
    try:
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1
        return sheet
    except Exception as e:
        logging.error(f"Error in getting Google Sheet: {str(e)}")
        raise

# Find the next empty row in the sheet
def find_next_empty_row(sheet):
    """
    Finds the next empty row in the sheet by checking the 'Дата и время' column.

    Args:
        sheet (gspread.models.Spreadsheet): Google Sheet client.

    Returns:
        int: The index of the next empty row.
    """
    try:
        str_list = list(filter(None, sheet.col_values(1)))  # Column A assumed to hold date/time
        return len(str_list) + 1
    except Exception as e:
        logging.error(f"Error finding next empty row: {str(e)}")
        raise

# Write data to the Google Sheet
def write_to_google_sheet(data: dict, sheet=None):
    """
    Writes the provided data to the Google Sheet.

    Args:
        data (dict): Data to write to the sheet.
        sheet (gspread.models.Spreadsheet, optional): Google Sheet client. If None, initializes it.

    Returns:
        str: Success message.
    """
    try:
        logging.info(f"Writing data to Google Sheet: {data}")

        # Extract fields directly from the dictionary
        raiting = data.get("overall_quality_rating", "")
        number_of_recommendations = data.get("number_of_recommendations", "")
        recommendations = data.get("criteria", [])

        # Text for recommendation
        recommendation_text = ""
        if recommendations:
            for criterion in recommendations:
                recommendation_text += f"{criterion.get('criterion_number')}: {criterion.get('recommendation')} \n"

        # If sheet is not provided, initialize it
        if sheet is None:
            sheet = get_google_sheet(SHEET_ID, CREDENTIALS_FILE)

        # Extract necessary fields from the data
        row_data = [
            data.get("date_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            data.get("manager", ""),
            1,
            data.get("call_duration", ""),
            data.get("conversion_to_sales", ""),
            raiting,
            number_of_recommendations,
            recommendation_text,
            data.get("kpi_actual", ""),
            data.get("kpi_plan", ""),
            data.get("deviation_from_plan", "")
        ]

        # Find the next empty row
        next_row = find_next_empty_row(sheet)

        # Write the row to Google Sheets
        sheet.insert_row(row_data, next_row)
        logging.info(f"Data successfully written to Google Sheet at row {next_row}")
        return "Data successfully written to Google Sheet"
    
    except Exception as e:
        logging.error(f"Error writing to Google Sheet: {str(e)}")
        return None
