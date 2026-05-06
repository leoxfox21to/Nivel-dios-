import os
from dotenv import load_dotenv
import pytz

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CUBA_TZ = pytz.timezone("America/Havana")

BALLDONTLIE_BASE = "https://www.balldontlie.io/api/v1"
NBA_STATS_BASE = "https://stats.nba.com/stats"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

NBA_STATS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.nba.com/",
    "Accept": "application/json",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}

REQUEST_TIMEOUT = 10
GROQ_MODEL = "llama3-70b-8192"
GROQ_MAX_TOKENS = 1024
