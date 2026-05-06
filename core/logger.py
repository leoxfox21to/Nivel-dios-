import logging
from datetime import datetime
from pathlib import Path
import pytz

CUBA_TZ = pytz.timezone("America/Havana")
LOG_FILE = Path(__file__).parent.parent / "picks_log.txt"


def setup_logging():
    """Configura el logging global de la aplicación."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def log_pick(home_team: str, away_team: str, pick_principal: str, confianza: str, riesgo: str):
    """Guarda el pick analizado en picks_log.txt."""
    now_cuba = datetime.now(CUBA_TZ).strftime("%Y-%m-%d %H:%M")
    line = (
        f"[{now_cuba} Cuba] {away_team} @ {home_team} | "
        f"PICK: {pick_principal} | "
        f"CONFIANZA: {confianza} | "
        f"RIESGO: {riesgo}\n"
    )
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error escribiendo en picks_log.txt: {e}")
