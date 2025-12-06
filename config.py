import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Google Sheets
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credential.json')
    SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'Registro_Movimientos')
    
    # General
    TIMEZONE = os.getenv('TIMEZONE', 'America/Argentina/Buenos_Aires')
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', 300))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Proveedores (configurable)
    PROVEEDORES = [
        "Distri", "Santa Rosa", "Tandil", "Pago Alquiler",
        "Servicios", "Limpieza"
    ]

config = Config()
