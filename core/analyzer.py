import asyncio
import logging
from datetime import datetime
import pytz

from apis import balldontlie, nba_stats, odds as odds_api
from config import CUBA_TZ

logger = logging.getLogger(__name__)


def estimate_pace(avg_points: float, avg_allowed: float) -> float:
    """Estimación simple de pace basada en puntos promedio."""
    return round((avg_points + avg_allowed) / 2.2, 1)


async def build_game_data(game: dict, all_odds: list) -> dict | None:
    """
    Recopila todos los datos necesarios para analizar un partido.
    Usa BallDontLie como fuente principal y stats.nba.com como respaldo.
    """
    home = game["home_team"]
    away = game["visitor_team"]
    home_id = home["id"]
    away_id = away["id"]
    home_name = home["full_name"]
    away_name = away["full_name"]

    # Convertir hora del partido a zona Cuba
    game_time_raw = game.get("status", "")
    try:
        utc_time = datetime.strptime(game_time_raw, "%I:%M %p ET")
        utc_time = utc_time.replace(tzinfo=pytz.timezone("US/Eastern"))
        cuba_time = utc_time.astimezone(CUBA_TZ).strftime("%I:%M %p")
    except Exception:
        cuba_time = game_time_raw

    # Recopilar datos en paralelo
    (
        home_last_10,
        away_last_10,
        home_avgs,
        away_avgs,
        home_b2b,
        away_b2b,
        h2h,
    ) = await asyncio.gather(
        balldontlie.get_team_last_10(home_id),
        balldontlie.get_team_last_10(away_id),
        balldontlie.get_team_avg_points(home_id),
        balldontlie.get_team_avg_points(away_id),
        balldontlie.is_back_to_back(home_id),
        balldontlie.is_back_to_back(away_id),
        balldontlie.get_h2h_last_5(home_id, away_id),
    )

    # Si BallDontLie no devuelve datos, intentar con stats.nba.com
    if not home_last_10:
        logger.warning(f"BallDontLie vacío para {home_name}, usando NBA Stats backup")
        home_log = await nba_stats.get_team_game_log(home_id)
        home_last_10 = ["W" if g.get("WL") == "W" else "L" for g in home_log]

    if not away_last_10:
        logger.warning(f"BallDontLie vacío para {away_name}, usando NBA Stats backup")
        away_log = await nba_stats.get_team_game_log(away_id)
        away_last_10 = ["W" if g.get("WL") == "W" else "L" for g in away_log]

    # Lesiones desde stats.nba.com
    injuries_raw = await nba_stats.get_injuries()
    home_injuries = []
    away_injuries = []
    for inj in injuries_raw:
        player_name = inj.get("PLAYER_NAME", "")
        team = inj.get("TEAM_ABBREVIATION", "")
        # Buscar por abreviatura del equipo (aproximación simple)
        injury_entry = {"name": player_name, "avg_points": 0.0, "status": inj.get("RETURN_DATE", "Out")}
        if home["abbreviation"] and home["abbreviation"] in team:
            home_injuries.append(injury_entry)
        elif away["abbreviation"] and away["abbreviation"] in team:
            away_injuries.append(injury_entry)

    # Cuotas de Pinnacle
    game_odds = odds_api.extract_game_odds(all_odds, home_name, away_name)

    home_avg_pts = home_avgs.get("avg_points", 0.0)
    home_avg_allow = home_avgs.get("avg_allowed", 0.0)
    away_avg_pts = away_avgs.get("avg_points", 0.0)
    away_avg_allow = away_avgs.get("avg_allowed", 0.0)

    return {
        "home_team": home_name,
        "away_team": away_name,
        "game_time": cuba_time,
        "home_last_10": home_last_10,
        "away_last_10": away_last_10,
        "home_avg_points": home_avg_pts,
        "away_avg_points": away_avg_pts,
        "home_avg_allowed": home_avg_allow,
        "away_avg_allowed": away_avg_allow,
        "home_pace": estimate_pace(home_avg_pts, home_avg_allow),
        "away_pace": estimate_pace(away_avg_pts, away_avg_allow),
        "home_is_back_to_back": home_b2b,
        "away_is_back_to_back": away_b2b,
        "home_injuries": home_injuries,
        "away_injuries": away_injuries,
        "over_under_line": game_odds["over_under_line"],
        "pinnacle_home_odds": game_odds["pinnacle_home_odds"],
        "pinnacle_away_odds": game_odds["pinnacle_away_odds"],
        "h2h_last_5": h2h,
    }
