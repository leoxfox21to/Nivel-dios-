from datetime import date, datetime
import pytz
from config import CUBA_TZ


def format_games_list(games: list, odds_data: list) -> str:
    """Formatea la lista de partidos del día en HTML para Telegram."""
    from apis.odds import extract_game_odds

    today = date.today().strftime("%d/%m/%Y")
    lines = [f"🏀 <b>PARTIDOS NBA HOY — {today}</b>", "━━━━━━━━━━━━━━━━━━━━━"]

    if not games:
        lines.append("No hay partidos NBA programados para hoy.")
        lines.append("\n<i>Si hay playoffs activos, puede que el calendario aún no esté cargado.</i>")
        return "\n".join(lines)

    for i, game in enumerate(games, start=1):
        home = game["home_team"]["full_name"]
        away = game["visitor_team"]["full_name"]
        status = game.get("status", "")

        game_odds = extract_game_odds(odds_data, home, away)
        ou_line = game_odds["over_under_line"]
        ou_text = f"O/U: {ou_line}" if ou_line else "O/U: N/D"

        lines.append(f"[{i}] {away} @ {home}")
        lines.append(f"    🕐 {status} | {ou_text}")

    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append("Usa /basket [número] para analizar un partido")
    return "\n".join(lines)


def format_analysis(game_data: dict, raw_analysis: str, warnings: list) -> str:
    """Formatea el análisis completo en HTML para Telegram."""
    home = game_data["home_team"]
    away = game_data["away_team"]
    now_cuba = datetime.now(CUBA_TZ).strftime("%I:%M %p")

    pick_principal = _extract_field(raw_analysis, "PICK PRINCIPAL")
    pick_secundaria = _extract_field(raw_analysis, "PICK SECUNDARIA")
    confianza = _extract_field(raw_analysis, "CONFIANZA")
    razonamiento = _extract_field(raw_analysis, "RAZONAMIENTO")
    riesgo = _extract_field(raw_analysis, "NIVEL DE RIESGO")

    warnings_text = "\n".join(f"  {w}" for w in warnings) if warnings else "  Ninguna"

    low_confidence_warning = ""
    try:
        conf_num = int(confianza.split("/")[0].strip())
        if conf_num < 6:
            low_confidence_warning = "\n⚠️ <b>Confianza baja — apuesta bajo tu propio riesgo</b>"
    except Exception:
        pass

    return (
        f"🏀 <b>ANÁLISIS — {away} @ {home}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>PICK PRINCIPAL:</b> {pick_principal}\n"
        f"📌 <b>PICK SECUNDARIA:</b> {pick_secundaria}\n"
        f"🎯 <b>CONFIANZA:</b> {confianza}\n"
        f"⚠️ <b>ADVERTENCIAS:</b>\n{warnings_text}\n"
        f"📝 <b>RAZONAMIENTO:</b> {razonamiento}\n"
        f"🔴 <b>RIESGO:</b> {riesgo}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ Analizado: {now_cuba} (Cuba)"
        f"{low_confidence_warning}"
    )


def _extract_field(text: str, field: str) -> str:
    """Extrae un campo específico de la respuesta de Groq."""
    for line in text.splitlines():
        if line.startswith(field + ":"):
            return line[len(field) + 1:].strip()
    return "N/D"


def extract_pick_info(raw_analysis: str) -> dict:
    """Extrae pick principal, confianza y riesgo para el logger."""
    return {
        "pick_principal": _extract_field(raw_analysis, "PICK PRINCIPAL"),
        "confianza": _extract_field(raw_analysis, "CONFIANZA"),
        "riesgo": _extract_field(raw_analysis, "NIVEL DE RIESGO"),
    }
