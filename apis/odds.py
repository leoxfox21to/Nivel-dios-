import httpx
from config import ODDS_API_BASE, ODDS_API_KEY, REQUEST_TIMEOUT
import logging

logger = logging.getLogger(__name__)


async def get_nba_odds() -> list:
    """Obtiene las cuotas NBA de Pinnacle via The Odds API."""
    url = f"{ODDS_API_BASE}/sports/basketball_nba/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "totals,h2h",
        "bookmakers": "pinnacle",
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"Odds API get_nba_odds error: {e}")
        return []


def extract_game_odds(odds_data: list, home_team: str, away_team: str) -> dict:
    """Extrae Over/Under y moneyline para un partido específico."""
    result = {
        "over_under_line": None,
        "pinnacle_home_odds": None,
        "pinnacle_away_odds": None,
    }

    def normalize(name: str) -> str:
        return name.lower().replace(" ", "")

    home_norm = normalize(home_team)
    away_norm = normalize(away_team)

    for game in odds_data:
        g_home = normalize(game.get("home_team", ""))
        g_away = normalize(game.get("away_team", ""))
        if home_norm in g_home or g_home in home_norm or away_norm in g_away or g_away in away_norm:
            for bookmaker in game.get("bookmakers", []):
                if bookmaker.get("key") == "pinnacle":
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "totals":
                            for outcome in market.get("outcomes", []):
                                if outcome["name"] == "Over":
                                    result["over_under_line"] = outcome.get("point")
                        if market["key"] == "h2h":
                            for outcome in market.get("outcomes", []):
                                if normalize(outcome["name"]) in g_home or g_home in normalize(outcome["name"]):
                                    result["pinnacle_home_odds"] = outcome.get("price")
                                elif normalize(outcome["name"]) in g_away or g_away in normalize(outcome["name"]):
                                    result["pinnacle_away_odds"] = outcome.get("price")
            break
    return result
