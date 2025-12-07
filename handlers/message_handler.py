from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup       
from telegram.ext import ContextTypes
from config import config
from utils.formatters import es_numero
from services.finance_service import finance_service
from db.sheets_manager import sheets_manager
from utils.formatters import formatear_monto
from datetime import datetime

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto"""
    try:
        texto = update.message.text.strip()

        # Si es un n√∫mero, REGISTRAR AUTOM√ÅTICAMENTE COMO CLIENTE
        if es_numero(texto):
            monto = float(texto.replace(",", "."))
            
            # Ì∂ï REGISTRAR COMO CLIENTE AUTOM√ÅTICAMENTE
            hora_actual = datetime.now().strftime("%H:%M")
            sheets_manager.registrar_ingreso(monto, hora=hora_actual)
            finance_service.invalidar_cache()
            
            # Obtener totales actualizados
            totales_dia = finance_service.totales_dia()
            totales_mes = finance_service.totales_mes()
            
            # Ì∂ï MOSTRAR 2 BOTONES: PROVEEDOR / GASTO
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Ì≤∏ Proveedor", callback_data=f"menu:proveedor:{monto}"),
                    InlineKeyboardButton("Ì∑æ Gasto", callback_data=f"menu:gasto:{monto}")
                ]
            ])

            await update.message.reply_text(
                f"‚úÖ Cliente: ${formatear_monto(monto)} ({hora_actual})\n"
                f"Ì≥Ü Total d√≠a: ${formatear_monto(totales_dia['clientes'])}\n"
                f"Ì≥ä Estado mes: ${formatear_monto(totales_mes['neto'])}\n\n"
                "¬øNecesit√°s registrar algo m√°s?",
                reply_markup=keyboard
            )
            return

        # Si no es n√∫mero, mostrar men√∫ de consultas
        keyboard = crear_menu_consultas()
        await update.message.reply_text(
            "Ì≥ä Eleg√≠ una opci√≥n:",
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"‚ùå Error en manejar_mensaje: {e}")
        await update.message.reply_text("‚ö†Ô∏è Ocurri√≥ un error, intent√° de nuevo.")

def crear_teclado_proveedores(monto):
    """Crea teclado con proveedores"""
    botones = []
    fila_temp = []

    # Proveedores en pares
    for proveedor in config.PROVEEDORES:
        fila_temp.append(
            InlineKeyboardButton(
                f"Ì≤∏ {proveedor}",
                callback_data=f"proveedor:{proveedor}:{monto}"
            )
        )

        if len(fila_temp) == 2:
            botones.append(fila_temp)
            fila_temp = []

    # Si qued√≥ proveedor suelto
    if fila_temp:
        botones.append(fila_temp)

    return InlineKeyboardMarkup(botones)

def crear_menu_consultas():
    """Crea men√∫ de consultas"""
    botones = [
        [InlineKeyboardButton("Ì≥• Ingreso hoy", callback_data="consulta:ingreso_hoy")],
        [InlineKeyboardButton("Ì≥§ Egreso hoy", callback_data="consulta:egreso_hoy")],
        [InlineKeyboardButton("Ì≥Ü Ingreso mes", callback_data="consulta:ingreso_mes")],
        [InlineKeyboardButton("Ì≥â Egreso mes", callback_data="consulta:egreso_mes")],
        [InlineKeyboardButton("Ì≤∞ Saldo mes", callback_data="consulta:saldo_mes")],
        [InlineKeyboardButton("Ì≤∏ Pagar Pendientes", callback_data="menu:pagar")],
        [InlineKeyboardButton("Ì≥ä Estad√≠sticas", callback_data="consulta:estadisticas")]
    ]
    return InlineKeyboardMarkup(botones)

