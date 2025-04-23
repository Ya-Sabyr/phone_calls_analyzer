import logging
import os
import glob
from openai import OpenAI

# Define directories for audio recordings and transcriptions
RECORDINGS_DIR = os.path.join('app', 'recordings', '*.mp3')
TRANSCRIPTIONS_DIR = os.path.join('app', 'transcriptions')

# Ensure the transcriptions directory exists
os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)

# Set up OpenAI API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Function to handle audio transcription using OpenAI's Whisper API
def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file using OpenAI Whisper API.
    
    Parameters:
    - audio_path (str): The path to the audio file.
    
    Returns:
    - str: The transcribed text, or None if an error occurs.
    """
    try:
        with open(audio_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return response.text
    except Exception as e:
        logging.error(f"Error during transcription of {audio_path}: {e}")
        return None

def process_recordings():
    """
    Task to process and transcribe all audio files in the recordings directory.
    This function is meant to be called asynchronously using Celery.
    """
    audio_files = glob.glob(RECORDINGS_DIR)
    if not audio_files:
        logging.info("No audio files found for transcription.")
        return
    
    for audio_file in audio_files:
        abs_path = os.path.abspath(audio_file)
        logging.info(f"Processing file: {audio_file}, absolute path: {abs_path}")
        
        if not os.path.exists(abs_path):
            logging.error(f"File not found: {abs_path}")
            continue

        # Transcribe the audio file using OpenAI API
        transcription = transcribe_audio(abs_path)
        if transcription:
            logging.info(f"Transcription for {audio_file}: {transcription}")
            
            # Generate the transcription file path
            base_name = os.path.basename(audio_file)
            transcribed_file_name = f"{os.path.splitext(base_name)[0]}_transcribed.txt"
            transcribed_file_path = os.path.join(TRANSCRIPTIONS_DIR, transcribed_file_name)
            
            # Save the transcription to a text file
            try:
                with open(transcribed_file_path, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                logging.info(f"Successfully saved transcription to {transcribed_file_path}")
            except Exception as e:
                logging.error(f"Failed to save transcription for {audio_file}. Error: {e}")
        else:
            logging.error(f"Failed to transcribe {audio_file}")
            
        # Remove the original audio file after processing
        try:
            os.remove(abs_path)
            logging.info(f"Successfully deleted file: {abs_path}")
        except Exception as e:
            logging.error(f"Failed to delete file {abs_path}. Error: {e}")

