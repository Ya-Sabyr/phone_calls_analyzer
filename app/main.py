import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# from src.auth.router import auth_router
# from src.bot.router import bot_routes
# from src.broadcast.router import broadcast_routes
# from src.chat.router import chat_routes
from app.webhook import webhook
from app.config import backend_config
# from src.database import init_db

app = FastAPI(debug=backend_config.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=backend_config.ALLOWED_HOSTS,  # List of allowed origins, use ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],  # List of allowed HTTP methods, use ["*"] to allow all
    allow_headers=["*"],  # List of allowed headers, use ["*"] to allow all
)

app. include_router(
    webhook, prefix="/webhook", tags=["webhook"]
)

@app.on_event("startup")
async def startup_event():
    
    
    backend_config.configure_logging()
    logging.info("Starting application...")
    logging.debug(f'Debug mode: {backend_config.DEBUG}')
    logging.info(f'Allowed hosts: {backend_config.ALLOWED_HOSTS}')
    
    # await init_db()