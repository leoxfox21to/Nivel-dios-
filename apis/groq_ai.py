import asyncio
import httpx
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_MAX_TOKENS, REQUEST_TIMEOUT
import logging

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def build_analysis_prompt(game_data: dict, warnings: list) -> str:
    """Construye el prompt exacto para enviar a Groq con todos los datos del partido."""
    return f"""
You are an elite NBA sports analyst with deep expertise in statistical betting analysis.
Analyze this NBA game and provide a precise betting recommendation.
Respond ONLY in Spanish. Be concise and direct.

GAME DATA:
- Matchup: {game_data['away_team']} @ {game_data['home_team']}
- Game time (Cuba): {game_data['game_time']}

TEAM STATS:
- {game_data['home_team']} last 10: {game_data['home_last_10']}
- {game_data['away_team']} last 10: {game_data['away_last_10']}
- {game_data['home_team']} avg points scored: {game_data['home_avg_points']} | allowed: {game_data['home_avg_allowed']}
- {game_data['away_team']} avg points scored: {game_data['away_avg_points']} | allowed: {game_data['away_avg_allowed']}
- {game_data['home_team']} pace: {game_data['home_pace']} possessions/game
- {game_data['away_team']} pace: {game_data['away_pace']} possessions/game

INJURIES:
- {game_data['home_team']}: {game_data['home_injuries']}
- {game_data['away_team']}: {game_data['away_injuries']}

BACK TO BACK:
- {game_data['home_team']}: {game_data['home_is_back_to_back']}
- {game_data['away_team']}: {game_data['away_is_back_to_back']}

MARKET:
- Pinnacle Over/Under line: {game_data['over_under_line']}
- Pinnacle home odds: {game_data['pinnacle_home_odds']}
- Pinnacle away odds: {game_data['pinnacle_away_odds']}

H2H LAST 5 MEETINGS:
{game_data['h2h_last_5']}

WARNINGS DETECTED:
{warnings}

YOUR TASK:
1. Calculate expected total points using pace + averages
2. Compare with Pinnacle line to find value
3. Analyze home/away advantage
4. Factor in injuries and back to back
5. Give ONE primary pick (Over/Under preferred) and ONE secondary pick (moneyline if clear value)

RESPOND IN THIS EXACT FORMAT:
PICK PRINCIPAL: [OVER/UNDER X.X puntos / [Equipo] ML]
PICK SECUNDARIA: [pick or "Sin pick secundaria"]
CONFIANZA: [1-10]/10
RAZONAMIENTO: [3-4 sentences max explaining the pick in Spanish]
NIVEL DE RIESGO: [BAJO / MEDIO / ALTO]
"""


async def analyze_game(game_data: dict, warnings: list) -> str:
    """Envía los datos del partido a Groq via HTTP y devuelve el análisis. Reintenta una vez si falla."""
    prompt = build_analysis_prompt(game_data, warnings)
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": GROQ_MAX_TOKENS,
        "temperature": 0.3,
    }

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq analyze_game error (intento {attempt + 1}): {e}")
            if attempt == 0:
                await asyncio.sleep(3)
            else:
                return "❌ Error al obtener análisis de IA. Intenta nuevamente en unos segundos."
