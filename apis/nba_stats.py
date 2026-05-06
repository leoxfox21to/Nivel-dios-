import httpx
from datetime import date
from config import NBA_STATS_BASE, NBA_STATS_HEADERS, REQUEST_TIMEOUT
import logging

logger = logging.getLogger(__name__)


async def get_today_games_backup() -> list:
    """Obtiene los partidos de hoy desde stats.nba.com como respaldo."""
    today = date.today().strftime("%m/%d/%Y")
    url = f"{NBA_STATS_BASE}/scoreboardv2"
    params = {"GameDate": today, "LeagueID": "00"}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=NBA_STATS_HEADERS) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            result_sets = data.get("resultSets", [])
            games = []
            for rs in result_sets:
                if rs.get("name") == "GameHeader":
                    headers = rs["headers"]
                    rows = rs["rowSet"]
                    for row in rows:
                        game = dict(zip(headers, row))
                        games.append(game)
            return games
    except Exception as e:
        logger.error(f"NBA Stats get_today_games_backup error: {e}")
        return []


async def get_team_game_log(team_id: int) -> list:
    """Obtiene el log de últimos partidos de un equipo desde stats.nba.com."""
    url = f"{NBA_STATS_BASE}/teamgamelog"
    params = {
        "TeamID": team_id,
        "Season": "2024-25",
        "SeasonType": "Regular Season",
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=NBA_STATS_HEADERS) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            result_sets = data.get("resultSets", [])
            for rs in result_sets:
                if rs.get("name") == "TeamGameLog":
                    headers = rs["headers"]
                    rows = rs["rowSet"]
                    return [dict(zip(headers, row)) for row in rows[:10]]
            return []
    except Exception as e:
        logger.error(f"NBA Stats get_team_game_log error: {e}")
        return []


async def get_injuries() -> list:
    """Obtiene el reporte de lesiones desde stats.nba.com."""
    url = f"{NBA_STATS_BASE}/injuries"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=NBA_STATS_HEADERS) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            result_sets = data.get("resultSets", [])
            for rs in result_sets:
                headers = rs.get("headers", [])
                rows = rs.get("rowSet", [])
                return [dict(zip(headers, row)) for row in rows]
            return []
    except Exception as e:
        logger.error(f"NBA Stats get_injuries error: {e}")
        return []
