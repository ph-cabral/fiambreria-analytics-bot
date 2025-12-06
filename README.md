# 🏪 Fiambrería Analytics Bot

Bot de Telegram para registro y análisis financiero automático de fiambrerías y pequeños comercios.

> ⚠️ **IMPORTANTE**: Este proyecto está en desarrollo activo. No usar en producción sin revisar la configuración de seguridad.

## 🎯 Características

- 📊 **Registro automático** de ingresos y egresos vía Telegram
- 💰 **Análisis en tiempo real** con pandas
- 📈 **Proyecciones financieras** basadas en histórico
- 🔔 **Notificaciones inteligentes** de pagos pendientes
- 📑 **Backup automático** en Google Sheets
- 🤖 **100% conversacional** - sin necesidad de apps adicionales

## 🛠️ Stack Tecnológico

- **Python 3.10+**
- **python-telegram-bot** - Interfaz con Telegram
- **pandas** - Análisis de datos
- **gspread** - Integración con Google Sheets
- **python-dotenv** - Gestión de configuración

## 📦 Instalación

### Prerequisitos

- Python 3.10 o superior
- Cuenta de Google Cloud (para Google Sheets API)
- Bot de Telegram (crear con [@BotFather](https://t.me/BotFather))

### Pasos

1. **Clonar repositorio**
```bash
git clone https://github.com/ph-cabral/fiambreria-analytics-bot.git
cd fiambreria-analytics-bot
