from dotenv import load_dotenv
import os

# Load environment variables from .env file if it exists
load_dotenv()

# Get API keys from environment variables with fallbacks for Cloud Run
NOTIF_API_KEY = os.getenv("NOTIF_API_KEY", "")
NOTIF_BASE_URL = os.getenv("NOTIF_BASE_URL", "")
