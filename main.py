from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters
from handlers import manejar_boton, manejar_mensaje
import os, logging
from dotenv import load_dotenv
from telegram import Update
import sys

# silenciar consola
# sys.stdout = open(os.devnull, 'w')
# sys.stderr = open(os.devnull, 'w')
# logging.disable(logging.CRITICAL)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.ERROR)  # Solo errores críticos

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()  # 🔥 Updates concurrentes
    
    app.add_handler(CallbackQueryHandler(manejar_boton))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    
    
    app.run_polling(
        timeout=60,
        read_timeout=60,
        write_timeout=60,
        connect_timeout=60,
        pool_timeout=60,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True  
    )
