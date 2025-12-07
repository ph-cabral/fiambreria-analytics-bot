# handlers/callback_handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from collections import deque

from services.finance_service import finance_service
from db.sheets_manager import sheets_manager
from utils.formatters import formatear_monto

# Anti-duplicaci√≥n
procesados = set()
ultimos_ingresos = deque(maxlen=5)

# ==================== NUEVAS FUNCIONES ====================

async def callback_menu_proveedor(query, data):
    """Muestra teclado de proveedores"""
    monto = float(data.split(":")[2])
    
    from handlers.message_handler import crear_teclado_proveedores
    keyboard = crear_teclado_proveedores(monto)
    
    await query.edit_message_text(
        f"Ì≤∞ Monto: ${formatear_monto(monto)}\n\n"
        "Seleccion√° el proveedor:",
        reply_markup=keyboard
    )

async def callback_menu_gasto(query, data):
    """Muestra opciones de gastos especiales"""
    monto = float(data.split(":")[2])
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ì∑ëÔ∏è Desperdicio", callback_data=f"gasto:desperdicio:{monto}")],
        [InlineKeyboardButton("Ì≤µ Gastos (100%)", callback_data=f"gasto:nosotros:{monto}")],
        [InlineKeyboardButton("Ì∑Ä Mercader√≠a (70%)", callback_data=f"gasto:mercaderia:{monto}")]
    ])
    
    await query.edit_message_text(
        f"Ì≤∞ Monto: ${formatear_monto(monto)}\n\n"
        "Seleccion√° el tipo de gasto:",
        reply_markup=keyboard
    )

async def callback_gasto(query, data):
    """Procesa gastos especiales"""
    partes = data.split(":")
    tipo_gasto = partes[1]
    monto_original = float(partes[2])
    
    hora_actual = datetime.now().strftime("%H:%M")
    
    if tipo_gasto == "desperdicio":
        sheets_manager.registrar_movimiento("Desperdicio", -abs(monto_original), hora=hora_actual, pagado=True)
        descripcion = "Ì∑ëÔ∏è Desperdicio"
        monto_final = monto_original
        
    elif tipo_gasto == "nosotros":
        sheets_manager.registrar_movimiento("Nosotros", -abs(monto_original), hora=hora_actual, pagado=True)
        descripcion = "ÌΩªÌ≤∏ Gastos (Nosotros)"
        monto_final = monto_original
        
    elif tipo_gasto == "mercaderia":
        monto_calculado = monto_original * 0.7
        sheets_manager.registrar_movimiento("Mercaderia", -abs(monto_calculado), hora=hora_actual, pagado=True)
        descripcion = "Ì∑ÄÌªí Mercader√≠a (70%)"
        monto_final = monto_calculado
    
    finance_service.invalidar_cache()
    
    totales_dia = finance_service.totales_dia()
    totales_mes = finance_service.totales_mes()
    
    mensaje = (
        f"‚úÖ {descripcion}\n"
        f"Ì≤∏ Monto: ${formatear_monto(monto_final)} ({hora_actual})\n"
        f"Ì≥Ü Total egresos d√≠a: ${formatear_monto(abs(totales_dia['egresos']))}\n"
        f"Ì≥ä Estado mes: ${formatear_monto(totales_mes['neto'])}"
    )
    
    await query.edit_message_text(mensaje)

# ==================== FUNCI√ìN PRINCIPAL ====================

async def manejar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja todos los callbacks de botones"""
    try:
        query = update.callback_query
        await query.answer()

        # Anti-duplicaci√≥n
        if query.id in procesados:
            return
        procesados.add(query.id)

        data = query.data
        print(f"Ì≥• Callback: {data}")

        # Ì∂ï NUEVAS RUTAS
        if data.startswith("menu:proveedor:"):
            await callback_menu_proveedor(query, data)
            return

        if data.startswith("menu:gasto:"):
            await callback_menu_gasto(query, data)
            return

        if data.startswith("gasto:"):
            await callback_gasto(query, data)
            return

        # RUTAS EXISTENTES
        if data.startswith("proveedor:"):
            await callback_proveedor(query, data)

        elif data.startswith("especial:"):
            await callback_especial(query, data)

        elif data.startswith("cliente:"):
            await callback_cliente(query, data)

        elif data.startswith("consulta:"):
            await callback_consulta(query, data)

        elif data == "menu:pagar":
            await callback_menu_pagar(query)

        elif data.startswith("pagar_idx:"):
            await callback_confirmar_pago(query, data)

        else:
            await query.edit_message_text("‚ùì Opci√≥n no reconocida")

    except Exception as e:
        print(f"‚ùå Error en callback: {e}")
        await query.edit_message_text("‚ö†Ô∏è Error al procesar")

# ==================== CALLBACKS EXISTENTES ====================

async def callback_proveedor(query, data):
    """Registra pago a proveedor"""
    _, proveedor, monto = data.split(":")
    monto = -abs(float(monto))

    hora_actual = datetime.now().strftime("%H:%M")

    sheets_manager.registrar_movimiento(proveedor, monto, hora=hora_actual, pagado=True)
    finance_service.invalidar_cache()

    totales_dia = finance_service.totales_dia()
    totales_mes = finance_service.totales_mes()
    total_prov = abs(finance_service.total_proveedor(proveedor))

    mensaje = (
        f"‚úÖ **PAGO REGISTRADO**\n\n"
        f"Ì≥§ Proveedor: {proveedor}\n"
        f"Ì≤∞ Monto: ${formatear_monto(abs(monto))}\n"
        f"Ìµê Hora: {hora_actual}\n\n"
        f"Ì≥ä Total a {proveedor} (mes): ${formatear_monto(total_prov)}\n\n"
        f"**HOY:**\n"
        f"Ì≤µ Ingresos: ${formatear_monto(totales_dia['ingresos'])}\n"
        f"Ì≤∏ Egresos: ${formatear_monto(abs(totales_dia['egresos']))}\n"
        f"Ì≥à Neto: ${formatear_monto(totales_dia['neto'])}\n\n"
        f"**MES:**\n"
        f"Ì≥Ö Saldo: ${formatear_monto(totales_mes['neto'])}"
    )

    await query.edit_message_text(mensaje)

async def callback_especial(query, data):
    """Registra categor√≠as especiales (Nosotros, Mercader√≠a, etc.)"""
    _, categoria, monto = data.split(":")
    monto = -abs(float(monto))

    hora_actual = datetime.now().strftime("%H:%M")

    sheets_manager.registrar_movimiento(categoria, monto, hora=hora_actual, pagado=True)
    finance_service.invalidar_cache()

    totales_dia = finance_service.totales_dia()

    mensaje = (
        f"‚úÖ **REGISTRADO: {categoria}**\n\n"
        f"Ì≤∞ Monto: ${formatear_monto(abs(monto))}\n"
        f"Ìµê Hora: {hora_actual}\n\n"
        f"Ì≥ä Saldo del d√≠a: ${formatear_monto(totales_dia['neto'])}"
    )

    await query.edit_message_text(mensaje)

async def callback_cliente(query, data):
    """Registra ingreso de cliente"""
    _, monto = data.split(":")
    monto_float = float(monto)

    timestamp_actual = datetime.now()
    for m, t in ultimos_ingresos:
        if m == monto_float and (timestamp_actual - t).total_seconds() < 60:
            await query.edit_message_text("‚úÖ Ese monto ya fue registrado recientemente")
            return

    hora_actual = timestamp_actual.strftime("%H:%M")

    sheets_manager.registrar_movimiento("cliente", monto_float, hora=hora_actual)
    ultimos_ingresos.append((monto_float, timestamp_actual))
    finance_service.invalidar_cache()

    totales_dia = finance_service.totales_dia()
    totales_mes = finance_service.totales_mes()

    mensaje = (
        f"‚úÖ **INGRESO REGISTRADO**\n\n"
        f"Ì≤∞ Monto: ${formatear_monto(monto_float)}\n"
        f"Ìµê Hora: {hora_actual}\n\n"
        f"**HOY:**\n"
        f"Ì≤µ Clientes: ${formatear_monto(totales_dia['clientes'])}\n"
        f"Ì≥à Total: ${formatear_monto(totales_dia['ingresos'])}\n\n"
        f"**MES:**\n"
        f"Ì≤∞ Clientes: ${formatear_monto(totales_mes['clientes'])}\n"
        f"Ì≥ä Saldo: ${formatear_monto(totales_mes['neto'])}"
    )

    await query.edit_message_text(mensaje)

async def callback_consulta(query, data):
    """Maneja consultas de reportes"""
    tipo = data.split(":")[1]

    if tipo == "ingreso_hoy":
        totales = finance_service.totales_dia()
        mensaje = (
            f"Ì≥• **INGRESOS DE HOY**\n\n"
            f"Ì≤∞ Total: ${formatear_monto(totales['ingresos'])}\n"
            f"Ì∑æ Clientes: ${formatear_monto(totales['clientes'])}\n"
            f"Ì≥ä Movimientos: {totales['cantidad_movimientos']}"
        )

    elif tipo == "egreso_hoy":
        totales = finance_service.totales_dia()
        mensaje = (
            f"Ì≥§ **EGRESOS DE HOY**\n\n"
            f"Ì≤∏ Total: ${formatear_monto(abs(totales['egresos']))}"
        )

    elif tipo == "ingreso_mes":
        totales = finance_service.totales_mes()
        mensaje = (
            f"Ì≥Ü **INGRESOS DEL MES**\n\n"
            f"Ì≤∞ Total: ${formatear_monto(totales['ingresos'])}\n"
            f"Ì∑æ Clientes: ${formatear_monto(totales['clientes'])}\n"
            f"Ì≥Ö D√≠as operativos: {totales['dias_operativos']}"
        )

    elif tipo == "egreso_mes":
        totales = finance_service.totales_mes()
        mensaje = (
            f"Ì≥â **EGRESOS DEL MES**\n\n"
            f"Ì≤∏ Total: ${formatear_monto(abs(totales['egresos']))}"
        )

    elif tipo == "saldo_mes":
        totales = finance_service.totales_mes()
        mensaje = (
            f"Ì≤∞ **SALDO DEL MES**\n\n"
            f"Ì≤µ Ingresos: ${formatear_monto(totales['ingresos'])}\n"
            f"Ì≤∏ Egresos: ${formatear_monto(abs(totales['egresos']))}\n"
            f"‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ‚îÅ\n"
            f"Ì≥ä **NETO: ${formatear_monto(totales['neto'])}**"
        )

    elif tipo == "estadisticas":
        stats = finance_service.estadisticas_avanzadas()

        if not stats:
            mensaje = "Ì≥ä No hay datos suficientes para estad√≠sticas"
        else:
            proy = stats['proyeccion']
            mensaje = (
                f"Ì≥ä **ESTAD√çSTICAS AVANZADAS**\n\n"
                f"Ì≤∞ Promedio venta/d√≠a: ${formatear_monto(stats['promedio_venta_diaria'])}\n"
                f"Ìºü Mejor d√≠a: {stats['mejor_dia']} (${formatear_monto(stats['mejor_dia_monto'])})\n"
                f"Ì≥Ö D√≠as operativos: {stats['dias_operativos']}\n\n"
                f"Ì¥Æ **PROYECCI√ìN FIN DE MES:**\n"
                f"Ì≤µ Ingresos: ${formatear_monto(proy['ingresos'])}\n"
                f"Ì≤∏ Egresos: ${formatear_monto(proy['egresos'])}\n"
                f"Ì≥à Neto: ${formatear_monto(proy['neto'])}\n\n"
                f"Ì≤∏ **TOP 5 GASTOS:**\n"
            )

            for prov, monto in stats['top_5_gastos'].items():
                mensaje += f"‚Ä¢ {prov}: ${formatear_monto(monto)}\n"

    else:
        mensaje = "‚ùì Consulta no reconocida"

    await query.edit_message_text(mensaje)

async def callback_menu_pagar(query):
    """Muestra men√∫ de egresos pendientes"""
    pendientes = finance_service.egresos_pendientes()

    if not pendientes:
        await query.edit_message_text("‚úÖ No hay egresos pendientes de pago")
        return

    botones = []
    for p in pendientes:
        texto = f"{p['proveedor']} - ${formatear_monto(abs(p['monto']))} ({p['fecha']})"
        botones.append([
            InlineKeyboardButton(texto, callback_data=f"pagar_idx:{p['fila_idx']}")
        ])

    await query.edit_message_text(
        f"Ì≤∏ **EGRESOS PENDIENTES** ({len(pendientes)})\n\n"
        "Seleccion√° para marcar como pagado:",
        reply_markup=InlineKeyboardMarkup(botones)
    )

async def callback_confirmar_pago(query, data):
    """Marca un egreso como pagado"""
    fila_idx = int(data.split(":")[1])

    try:
        proveedor, monto = sheets_manager.marcar_como_pagado(fila_idx)
        finance_service.invalidar_cache()

        mensaje = (
            f"‚úÖ **MARCADO COMO PAGADO**\n\n"
            f"Ì≥§ Proveedor: {proveedor}\n"
            f"Ì≤∞ Monto: ${formatear_monto(abs(monto))}"
        )

        await query.edit_message_text(mensaje)

    except Exception as e:
        await query.edit_message_text(f"‚ùå Error al marcar como pagado: {e}")

