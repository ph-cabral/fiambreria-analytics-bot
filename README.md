# 🏪 Fiambrería Analytics Bot

Bot de Telegram para registro y análisis financiero automático de fiambrerías y comercios pequeños.

## 🎯 Características

- 📊 Registro de ingresos y egresos en tiempo real
- 💰 Cálculo automático de flujo de caja (diario/mensual)
- 📈 Análisis con pandas y proyecciones
- 🔔 Notificaciones de pagos pendientes
- 📑 Almacenamiento en Google Sheets
- 🤖 100% automatizado vía Telegram

## 🚀 Stack Tecnológico

- Python 3.10+
- python-telegram-bot
- pandas
- gspread (Google Sheets API)
- systemd (deploy)

## 📦 Instalación

```bash
# Clonar repo
git clone https://github.com/tu-usuario/fiambreria-analytics-bot.git
cd fiambreria-analytics-bot

# Entorno virtual
python3 -m venv venv
source venv/bin/activate

# Dependencias
pip install -r requirements.txt

# Configurar .env (ver .env.example)
cp .env.example .env
nano .env

# Ejecutar
python main.py

