from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from handlers import manejar_boton, manejar_mensaje
import os, sys, logging
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update


# Silenciar consola por completo
# sys.stdout = open(os.devnull, 'w')
# sys.stderr = open(os.devnull, 'w')
# logging.disable(logging.CRITICAL)


load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)

class NetworkErrorFilter(logging.Filter):
    def filter(self, record):
        return "NetworkError" not in record.getMessage()

logging.getLogger("telegram.ext._application").addFilter(NetworkErrorFilter())
logging.getLogger("telegram.ext._updater").addFilter(NetworkErrorFilter())


if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CallbackQueryHandler(manejar_boton))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    app.run_polling(timeout=300, read_timeout=300, write_timeout=300, connect_timeout=300, pool_timeout=300, allowed_updates=Update.ALL_TYPES)