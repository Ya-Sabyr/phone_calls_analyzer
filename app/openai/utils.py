import json
import logging
import os

from openai import OpenAI
from app.integrations.gspred import write_to_google_sheet

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
client = OpenAI(api_key=OPENAI_API_KEY)

# Define the directory for transcriptions
TRANSCRIPTIONS_DIR = os.path.join('app', 'transcriptions')

def clean_openai_response(response_text: str) -> str:
    """
    Clean the OpenAI response by removing markdown and extracting the JSON.
    """
    logging.info("Starting to clean the OpenAI response.")
    
    # Remove markdown ticks and clean the response
    cleaned_response = response_text.strip().strip("```").replace("```json", "").strip()
    
    # We assume valid JSON is between the first '[' and the last ']', so extract the JSON part
    json_start = cleaned_response.find("[")
    json_end = cleaned_response.rfind("]")
    
    if json_start == -1 or json_end == -1:
        logging.error("Invalid response: No JSON data found.")
        return None
    
    # Extract the JSON part of the response
    json_part = cleaned_response[json_start:json_end + 1]
    
    logging.info("Successfully cleaned the OpenAI response and extracted JSON part.")
    
    return json_part

def extract_recommendations(response_text: str, call_detail: dict):
    """
    Extract the recommendations and additional details from the OpenAI response.
    """
    logging.info("Starting extraction of recommendations.")
    
    try:
        # Clean the response to get the JSON part
        json_part = clean_openai_response(response_text)
        
        if json_part is None:
            logging.error("Invalid response: No JSON data found.")
            return None
        
        # Parse the JSON data
        recommendations_data = json.loads(json_part)
        
        logging.info("Successfully parsed JSON data.")
        
        # Extract criteria information
        extracted_info = []
        for criterion in recommendations_data:
            score = criterion['score']
            if criterion['score'] >= 0.4:
                continue
            extracted_info.append({
                "criterion_number": criterion["criterion_number"],
                "criterion_description": criterion["criterion_description"],
                "score": criterion["score"],
                "explanation": criterion["explanation"],
                "recommendation": criterion["recommendation"]
            })
        
        logging.info(f"Extracted {len(extracted_info)} recommendation criteria.")
        
        # Extract conversation summary, overall rating, and number of recommendations
        summary_index = response_text.find("Conversation summary: ")
        overall_rating_index = response_text.find("Overall quality rating (out of 10): ")
        num_recommendations_index = response_text.find("Number of recommendations: ")

        # Extract the plain text data following the JSON part
        conversation_summary = response_text[summary_index:].split("Conversation summary: ")[1].split("\n")[0].strip()
        overall_rating = response_text[overall_rating_index:].split("Overall quality rating (out of 10): ")[1].split("\n")[0].strip()
        num_recommendations = response_text[num_recommendations_index:].split("Number of recommendations: ")[1].split("\n")[0].strip()
        
        logging.info("Successfully extracted conversation summary, overall rating, and number of recommendations.")
        
        # Return structured data
        return {
            "criteria": extracted_info,
            "conversation_summary": conversation_summary,
            "overall_quality_rating": float(overall_rating),
            "number_of_recommendations": int(num_recommendations),
            "manager": call_detail.get("manager"),
            "call_duration": call_detail.get("call_duration"),
        }
    
    except Exception as e:
        logging.error(f"Error while extracting recommendations: {e}")
        return None

def run_recommendations(call_details: list):
    """
    Check all files in the transcriptions directory, use them as 'transcribed text', 
    and get recommendations from OpenAI assistant.
    """
    logging.info("Starting to process transcription files for recommendations.")
    
    # Check if the transcriptions directory exists and has files
    if not os.path.exists(TRANSCRIPTIONS_DIR):
        logging.error(f"Transcriptions directory '{TRANSCRIPTIONS_DIR}' not found.")
        raise FileNotFoundError(f"Transcriptions directory '{TRANSCRIPTIONS_DIR}' not found.")
    
    transcription_files = [f for f in os.listdir(TRANSCRIPTIONS_DIR) if f.endswith('.txt')]
    
    if not transcription_files:
        logging.error("No transcription files found in the directory.")
        raise FileNotFoundError("No transcription files found in the directory.")
    
    for transcription_file, call_detail in zip(transcription_files, call_details):
        transcription_path = os.path.join(TRANSCRIPTIONS_DIR, transcription_file)
        
        logging.info(f"Processing file: {transcription_file}")
        
        # Read the content of the transcription file
        with open(transcription_path, 'r', encoding='utf-8') as file:
            transcribed_text = file.read()
        
        # Create and run the assistant thread for the transcribed text
        run = client.beta.threads.create_and_run_poll(
            assistant_id=OPENAI_ASSISTANT_ID,
            thread={
                "messages": [
                    {"role": "user", "content": transcribed_text}
                ]
            }
        )
        
        thread_id = run.thread_id
        
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        openai_response = messages.data[0].content[0].text.value
        
        logging.info(f"Received OpenAI response for file: {transcription_file}")
        
        # Extract and parse the generated JSON text
        recommendations = extract_recommendations(openai_response, call_detail)

        write_to_google_sheet(recommendations)

        try:
            os.remove(transcription_path)
            logging.info(f"Successfully deleted file: {transcription_path}")
        except Exception as e:
            logging.error(f"Failed to delete file {transcription_path}. Error: {e}")

