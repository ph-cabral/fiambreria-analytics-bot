import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import config
from handlers.message_handler import manejar_mensaje
from handlers.callback_handler import manejar_callback

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if config.DEBUG else logging.WARNING
)

logger = logging.getLogger(__name__)

async def cmd_start(update, context):
    """Comando /start"""
    await update.message.reply_text(
        "🏪 **Bot de Fiambrería**\n\n"
        "Enviá un monto para registrar un movimiento.\n"
        "Ejemplo: 1500"
    )

async def cmd_help(update, context):
    """Comando /help"""
    await update.message.reply_text(
        "📖 **AYUDA**\n\n"
        "• Enviá un número para registrar movimiento\n"
        "• Elegí si es ingreso o egreso\n"
        "• Consultá reportes desde el menú\n\n"
        "Comandos:\n"
        "/start - Inicio\n"
        "/help - Esta ayuda"
    )

def main():
    """Función principal"""
    
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN no configurado en .env")
        return
    
    # Crear aplicación
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    app.add_handler(CallbackQueryHandler(manejar_callback))
    
    # Iniciar bot
    print("🚀 Bot iniciado correctamente")
    print(f"📊 Spreadsheet: {config.SPREADSHEET_NAME}")
    print(f"⏰ Caché: {config.CACHE_DURATION}s")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
