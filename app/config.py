import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Telegram API credentials
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tgupload.db") 