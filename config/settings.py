import os
from dotenv import load_dotenv

load_dotenv()

# Bot sozlamalari
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "")

# Limitlar
MAX_SEARCH_RESULTS = 5
MAX_POST_LENGTH = 4000
DAILY_LIMIT = 20

# Avtomatik posting (True/False)
AUTO_POST_ENABLED = os.getenv("AUTO_POST_ENABLED", "True").lower() == "true"