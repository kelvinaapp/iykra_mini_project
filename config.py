from dotenv import load_dotenv
import os

load_dotenv()

NOTIF_API_KEY = os.getenv("NOTIF_API_KEY")
NOTIF_BASE_URL = os.getenv("NOTIF_BASE_URL")
