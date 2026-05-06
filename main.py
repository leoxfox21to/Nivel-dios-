import logging
from telegram.ext import ApplicationBuilder, CommandHandler

from config import TELEGRAM_BOT_TOKEN, CUBA_TZ
from core.logger import setup_logging
from bot.handlers import cmd_start, cmd_help, cmd_basket

def main():
    """Punto de entrada principal del bot."""
    setup_logging()
    logger = logging.getLogger(__name__)

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN no configurado en .env")
        raise ValueError("Falta TELEGRAM_BOT_TOKEN en el archivo .env")

    logger.info("Iniciando Nivel Dios Picks Bot...")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("basket", cmd_basket))

    logger.info(f"Bot activo — Zona horaria: {CUBA_TZ.zone}")
    logger.info("Escuchando comandos... Presiona Ctrl+C para detener.")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
