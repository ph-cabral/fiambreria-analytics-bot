from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import config
from utils.formatters import es_numero

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto"""
    try:
        texto = update.message.text.strip()
        
        # Si es un número, mostrar teclado de proveedores
        if es_numero(texto):
            monto = float(texto.replace(",", "."))
            keyboard = crear_teclado_proveedores(monto)
            
            await update.message.reply_text(
                f"💰 Monto: ${monto:,.2f}\n\n"
                "Seleccioná el destino:",
                reply_markup=keyboard
            )
            return
        
        # Si no es número, mostrar menú de consultas
        keyboard = crear_menu_consultas()
        await update.message.reply_text(
            "📊 Elegí una opción:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        print(f"❌ Error en manejar_mensaje: {e}")
        await update.message.reply_text("⚠️ Ocurrió un error, intentá de nuevo.")

def crear_teclado_proveedores(monto):
    """Crea teclado con proveedores y opciones especiales"""
    botones = []
    fila_temp = []
    
    # Proveedores en pares
    for proveedor in config.PROVEEDORES:
        fila_temp.append(
            InlineKeyboardButton(
                f"💸 {proveedor}", 
                callback_data=f"proveedor:{proveedor}:{monto}"
            )
        )
        
        if len(fila_temp) == 2:
            botones.append(fila_temp)
            fila_temp = []
    
    # Si quedó proveedor suelto, agregar botón de "Pagar"
    if fila_temp:
        fila_temp.append(
            InlineKeyboardButton("✅ Pagar Pendiente", callback_data="menu:pagar")
        )
        botones.append(fila_temp)
        fila_temp = []
    
    # Botones especiales
    botones.extend([
        [
            InlineKeyboardButton("🍻💸 Nosotros", callback_data=f"especial:Nosotros:{monto}"),
            InlineKeyboardButton("🧀🛒 Mercadería", callback_data=f"especial:Mercaderia:{monto}")
        ],
        [
            InlineKeyboardButton("🗑️ Desperdicio", callback_data=f"especial:Desperdicio:{monto}"),
            InlineKeyboardButton("📦 Corrección", callback_data=f"especial:Correccion:{monto}")
        ],
        [
            InlineKeyboardButton("🧾 Cliente", callback_data=f"cliente:{monto}")
        ]
    ])
    
    return InlineKeyboardMarkup(botones)

def crear_menu_consultas():
    """Crea menú de consultas"""
    botones = [
        [InlineKeyboardButton("📥 Ingreso hoy", callback_data="consulta:ingreso_hoy")],
        [InlineKeyboardButton("📤 Egreso hoy", callback_data="consulta:egreso_hoy")],
        [InlineKeyboardButton("📆 Ingreso mes", callback_data="consulta:ingreso_mes")],
        [InlineKeyboardButton("📉 Egreso mes", callback_data="consulta:egreso_mes")],
        [InlineKeyboardButton("💰 Saldo mes", callback_data="consulta:saldo_mes")],
        [InlineKeyboardButton("💸 Pagar Pendientes", callback_data="menu:pagar")],
        [InlineKeyboardButton("📊 Estadísticas", callback_data="consulta:estadisticas")]
    ]
    return InlineKeyboardMarkup(botones)
