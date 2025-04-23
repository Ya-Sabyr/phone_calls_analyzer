import logging
from fastapi import APIRouter, Request, HTTPException

webhook = APIRouter()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@webhook.post("/")
async def bitrix_webhook(request: Request):
    try:
        # Parse the incoming request as JSON
        payload = await request.json()
        
        # Log the received payload
        logger.info("Received webhook from Bitrix: %s", payload)
        
        # Process the webhook payload (you can add your own logic here)
        # For example, handle specific events or actions
        event_type = payload.get('event', 'unknown')
        logger.info(f"Processing event: {event_type}")
        
        # Return a success response back to Bitrix
        return {"status": "success", "message": "Webhook received and processed"}
    
    except Exception as e:
        logger.error(f"Error processing Bitrix webhook: {e}")
        raise HTTPException(status_code=400, detail="Failed to process webhook")

