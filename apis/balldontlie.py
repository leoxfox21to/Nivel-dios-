import httpx
from datetime import date, timedelta
from config import BALLDONTLIE_BASE, BALLDONTLIE_API_KEY, REQUEST_TIMEOUT
import logging

logger = logging.getLogger(__name__)


def _headers() -> dict:
    """Headers para BallDontLie v2 — requiere clave de autorización."""
    return {"Authorization": BALLDONTLIE_API_KEY} if BALLDONTLIE_API_KEY else {}


async def get_today_games() -> list:
    """Obtiene los partidos de NBA de hoy desde BallDontLie v2."""
    today = date.today().isoformat()
    url = f"{BALLDONTLIE_BASE}/games"
    params = {"dates[]": today, "per_page": 100}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            return resp.json().get("data", [])
    except Exception as e:
        logger.error(f"BallDontLie get_today_games error: {e}")
        return []


async def get_team_last_10(team_id: int) -> list:
    """Obtiene los últimos 10 resultados de un equipo."""
    today = date.today()
    start_date = (today - timedelta(days=90)).isoformat()
    url = f"{BALLDONTLIE_BASE}/games"
    params = {
        "team_ids[]": team_id,
        "start_date": start_date,
        "end_date": today.isoformat(),
        "per_page": 100,
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            games = resp.json().get("data", [])
            finished = [g for g in games if g.get("status") == "Final"]
            finished_sorted = sorted(finished, key=lambda g: g["date"], reverse=True)[:10]
            results = []
            for g in finished_sorted:
                home_id = g["home_team"]["id"]
                home_score = g["home_team_score"]
                away_score = g["visitor_team_score"]
                if team_id == home_id:
                    results.append("W" if home_score > away_score else "L")
                else:
                    results.append("W" if away_score > home_score else "L")
            return results
    except Exception as e:
        logger.error(f"BallDontLie get_team_last_10 error: {e}")
        return []


async def get_team_avg_points(team_id: int) -> dict:
    """Calcula promedio de puntos anotados y permitidos en últimos 10 juegos."""
    today = date.today()
    start_date = (today - timedelta(days=90)).isoformat()
    url = f"{BALLDONTLIE_BASE}/games"
    params = {
        "team_ids[]": team_id,
        "start_date": start_date,
        "end_date": today.isoformat(),
        "per_page": 100,
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            games = resp.json().get("data", [])
            finished = [g for g in games if g.get("status") == "Final"]
            finished_sorted = sorted(finished, key=lambda g: g["date"], reverse=True)[:10]
            scored, allowed = [], []
            for g in finished_sorted:
                if g["home_team"]["id"] == team_id:
                    scored.append(g["home_team_score"])
                    allowed.append(g["visitor_team_score"])
                else:
                    scored.append(g["visitor_team_score"])
                    allowed.append(g["home_team_score"])
            avg_scored = round(sum(scored) / len(scored), 1) if scored else 0.0
            avg_allowed = round(sum(allowed) / len(allowed), 1) if allowed else 0.0
            return {"avg_points": avg_scored, "avg_allowed": avg_allowed}
    except Exception as e:
        logger.error(f"BallDontLie get_team_avg_points error: {e}")
        return {"avg_points": 0.0, "avg_allowed": 0.0}


async def is_back_to_back(team_id: int) -> bool:
    """Determina si el equipo jugó ayer."""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    url = f"{BALLDONTLIE_BASE}/games"
    params = {"team_ids[]": team_id, "dates[]": yesterday}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            return len(resp.json().get("data", [])) > 0
    except Exception as e:
        logger.error(f"BallDontLie is_back_to_back error: {e}")
        return False


async def get_h2h_last_5(home_team_id: int, away_team_id: int) -> list:
    """Obtiene los últimos 5 enfrentamientos directos entre dos equipos."""
    url = f"{BALLDONTLIE_BASE}/games"
    params = {
        "team_ids[]": [home_team_id, away_team_id],
        "per_page": 100,
        "seasons[]": [2022, 2023, 2024],
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            games = resp.json().get("data", [])
            h2h = [
                g for g in games
                if g.get("status") == "Final"
                and {g["home_team"]["id"], g["visitor_team"]["id"]} == {home_team_id, away_team_id}
            ]
            h2h_sorted = sorted(h2h, key=lambda g: g["date"], reverse=True)[:5]
            results = []
            for g in h2h_sorted:
                total = g["home_team_score"] + g["visitor_team_score"]
                winner = (
                    g["home_team"]["full_name"]
                    if g["home_team_score"] > g["visitor_team_score"]
                    else g["visitor_team"]["full_name"]
                )
                results.append({
                    "date": g["date"][:10],
                    "winner": winner,
                    "total_points": total,
                    "score": f"{g['home_team_score']}-{g['visitor_team_score']}",
                })
            return results
    except Exception as e:
        logger.error(f"BallDontLie get_h2h_last_5 error: {e}")
        return []
