import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from apis import balldontlie, nba_stats, odds as odds_api
from apis.groq_ai import analyze_game
from core.analyzer import build_game_data
from core.filters import apply_filters
from core.logger import log_pick
from bot.formatter import format_games_list, format_analysis, extract_pick_info

logger = logging.getLogger(__name__)

# Almacena los partidos del día en memoria para la sesión
_games_cache: list = []
_odds_cache: list = []


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start — Mensaje de bienvenida."""
    text = (
        "🏀 <b>Bienvenido a Nivel Dios Picks</b>\n"
        "El sistema de análisis NBA más preciso.\n\n"
        "Comandos disponibles:\n"
        "/basket — Ver partidos de hoy\n"
        "/basket [número] — Analizar partido\n"
        "/help — Ayuda"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help — Ayuda en español."""
    text = (
        "🏀 <b>Ayuda — Nivel Dios Picks</b>\n\n"
        "📋 <b>Comandos:</b>\n\n"
        "• /start — Mensaje de bienvenida\n"
        "• /basket — Lista todos los partidos NBA de hoy con cuota O/U\n"
        "• /basket [número] — Analiza el partido seleccionado con IA\n"
        "• /help — Muestra esta ayuda\n\n"
        "⚙️ <b>Cómo funciona:</b>\n"
        "1. Usa /basket para ver los partidos de hoy\n"
        "2. Elige el número del partido que quieres analizar\n"
        "3. Escribe /basket 1 (o el número correspondiente)\n"
        "4. El bot recopila estadísticas, lesiones y cuotas de Pinnacle\n"
        "5. La IA analiza todo y entrega el pick en español\n\n"
        "📊 <b>Fuentes de datos:</b>\n"
        "• BallDontLie API v2 — Estadísticas y resultados\n"
        "• The Odds API — Partidos y cuotas de Pinnacle\n"
        "• Groq AI (llama3-70b) — Análisis inteligente"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /basket — Sin argumentos muestra la lista de partidos.
    Con número (/basket 1) analiza el partido seleccionado.
    """
    global _games_cache, _odds_cache

    args = context.args

    # Sin argumento: mostrar lista de partidos
    if not args:
        await update.message.reply_text("⏳ Obteniendo partidos de hoy...")
        try:
            # Obtener cuotas primero (fuente más confiable actualmente)
            odds_data = await odds_api.get_nba_odds()

            # Intentar BallDontLie primero
            games = await balldontlie.get_today_games()

            # Si BallDontLie falla, intentar NBA Stats
            if not games:
                logger.warning("BallDontLie sin datos, probando NBA Stats backup")
                games = await nba_stats.get_today_games_backup()

            # Si ambos fallan pero hay odds, construir partidos desde odds
            if not games and odds_data:
                logger.warning("BallDontLie y NBA Stats sin datos — usando The Odds API como fuente de partidos")
                games = balldontlie.build_games_from_odds(odds_data)

            _games_cache = games
            _odds_cache = odds_data

            msg = format_games_list(games, odds_data)
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

        except Exception as e:
            logger.error(f"cmd_basket list error: {e}")
            await update.message.reply_text(
                "❌ Error al obtener partidos. Verifica que las claves en .env sean correctas e intenta de nuevo."
            )
        return

    # Con argumento: analizar partido específico
    try:
        game_num = int(args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Número inválido. Ejemplo: /basket 1"
        )
        return

    if not _games_cache:
        await update.message.reply_text(
            "⚠️ Primero usa /basket para cargar los partidos de hoy."
        )
        return

    if game_num < 1 or game_num > len(_games_cache):
        await update.message.reply_text(
            f"❌ Número fuera de rango. Hay {len(_games_cache)} partidos hoy."
        )
        return

    game = _games_cache[game_num - 1]
    home = game["home_team"]["full_name"]
    away = game["visitor_team"]["full_name"]

    await update.message.reply_text(f"⏳ Analizando {away} @ {home}...")

    try:
        if not _odds_cache:
            _odds_cache = await odds_api.get_nba_odds()

        game_data = await build_game_data(game, _odds_cache)

        if game_data is None:
            await update.message.reply_text(
                "⚠️ No se pudo obtener datos suficientes para este partido."
            )
            return

        filter_result = apply_filters(game_data)

        if filter_result["skip"]:
            warnings_text = "\n".join(f"• {w}" for w in filter_result["warnings"])
            await update.message.reply_text(
                f"⚠️ <b>Datos insuficientes. No se recomienda apostar.</b>\n\n"
                f"<b>Razones:</b>\n{warnings_text}",
                parse_mode=ParseMode.HTML,
            )
            return

        raw_analysis = await analyze_game(game_data, filter_result["warnings"])
        msg = format_analysis(game_data, raw_analysis, filter_result["warnings"])
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

        pick_info = extract_pick_info(raw_analysis)
        log_pick(
            home_team=home,
            away_team=away,
            pick_principal=pick_info["pick_principal"],
            confianza=pick_info["confianza"],
            riesgo=pick_info["riesgo"],
        )

    except Exception as e:
        logger.error(f"cmd_basket analyze error: {e}")
        await update.message.reply_text(
            "❌ Error al analizar el partido. Intenta de nuevo en unos segundos."
        )
