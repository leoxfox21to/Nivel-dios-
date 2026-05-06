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
            data = resp.json().get("data", [])
            logger.info(f"BallDontLie devolvió {len(data)} partidos para hoy")
            return data
    except Exception as e:
        logger.error(f"BallDontLie get_today_games error: {e}")
        return []


def build_games_from_odds(odds_data: list) -> list:
    """
    Construye una lista de partidos sintéticos desde The Odds API.
    Úsalo cuando BallDontLie no devuelve datos (playoffs, offseason, etc.).
    El formato imita la estructura de BallDontLie para compatibilidad.
    """
    games = []
    for i, game in enumerate(odds_data):
        home_name = game.get("home_team", "")
        away_name = game.get("away_team", "")
        commence = game.get("commence_time", "")

        if not home_name or not away_name:
            continue

        games.append({
            "_from_odds": True,
            "_odds_id": game.get("id", str(i)),
            "id": i + 1,
            "home_team": {
                "id": -(i * 2 + 1),
                "full_name": home_name,
                "abbreviation": _abbrev(home_name),
            },
            "visitor_team": {
                "id": -(i * 2 + 2),
                "full_name": away_name,
                "abbreviation": _abbrev(away_name),
            },
            "status": commence,
            "home_team_score": 0,
            "visitor_team_score": 0,
        })
    return games


def _abbrev(full_name: str) -> str:
    """Genera abreviatura a partir del nombre completo del equipo."""
    words = full_name.split()
    if len(words) >= 2:
        return words[-1][:3].upper()
    return full_name[:3].upper()


async def get_team_last_10(team_id: int) -> list:
    """
    Obtiene los últimos 10 resultados de un equipo.
    Si team_id es negativo (partido sintético de odds), devuelve lista vacía.
    """
    if team_id < 0:
        logger.info(f"Equipo sintético (id={team_id}), sin historial en BallDontLie")
        return []

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
    """
    Calcula promedio de puntos anotados y permitidos en últimos 10 juegos.
    Si team_id es negativo (partido sintético), devuelve ceros.
    """
    if team_id < 0:
        return {"avg_points": 0.0, "avg_allowed": 0.0}

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
    """
    Determina si el equipo jugó ayer.
    Si team_id es negativo (partido sintético), devuelve False.
    """
    if team_id < 0:
        return False

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
    """
    Obtiene los últimos 5 enfrentamientos directos entre dos equipos.
    Si algún id es negativo (partido sintético), devuelve lista vacía.
    """
    if home_team_id < 0 or away_team_id < 0:
        return []

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
