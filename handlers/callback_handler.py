from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from collections import deque

from services.finance_service import finance_service
from db.sheets_manager import sheets_manager
from utils.formatters import formatear_monto

# Anti-duplicación
procesados = set()
ultimos_ingresos = deque(maxlen=5)

async def manejar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja todos los callbacks de botones"""
    try:
        query = update.callback_query
        await query.answer()
        
        # Anti-duplicación
        if query.id in procesados:
            return
        procesados.add(query.id)
        
        data = query.data
        print(f"📥 Callback: {data}")
        
        # RUTAS
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
            await query.edit_message_text("❓ Opción no reconocida")
            
    except Exception as e:
        print(f"❌ Error en callback: {e}")
        await query.edit_message_text("⚠️ Error al procesar")

async def callback_proveedor(query, data):
    """Registra pago a proveedor"""
    _, proveedor, monto = data.split(":")
    monto = -abs(float(monto))
    
    hora_actual = datetime.now().strftime("%H:%M")
    
    # Registrar
    sheets_manager.registrar_movimiento(proveedor, monto, hora=hora_actual, pagado=True)
    finance_service.invalidar_cache()
    
    # Obtener totales
    totales_dia = finance_service.totales_dia()
    totales_mes = finance_service.totales_mes()
    total_prov = abs(finance_service.total_proveedor(proveedor))
    
    mensaje = (
        f"✅ **PAGO REGISTRADO**\n\n"
        f"📤 Proveedor: {proveedor}\n"
        f"💰 Monto: ${formatear_monto(abs(monto))}\n"
        f"🕐 Hora: {hora_actual}\n\n"
        f"📊 Total a {proveedor} (mes): ${formatear_monto(total_prov)}\n\n"
        f"**HOY:**\n"
        f"💵 Ingresos: ${formatear_monto(totales_dia['ingresos'])}\n"
        f"💸 Egresos: ${formatear_monto(abs(totales_dia['egresos']))}\n"
        f"📈 Neto: ${formatear_monto(totales_dia['neto'])}\n\n"
        f"**MES:**\n"
        f"📅 Saldo: ${formatear_monto(totales_mes['neto'])}"
    )
    
    await query.edit_message_text(mensaje)

async def callback_especial(query, data):
    """Registra categorías especiales (Nosotros, Mercadería, etc.)"""
    _, categoria, monto = data.split(":")
    monto = -abs(float(monto))
    
    hora_actual = datetime.now().strftime("%H:%M")
    
    sheets_manager.registrar_movimiento(categoria, monto, hora=hora_actual, pagado=True)
    finance_service.invalidar_cache()
    
    totales_dia = finance_service.totales_dia()
    
    mensaje = (
        f"✅ **REGISTRADO: {categoria}**\n\n"
        f"💰 Monto: ${formatear_monto(abs(monto))}\n"
        f"🕐 Hora: {hora_actual}\n\n"
        f"📊 Saldo del día: ${formatear_monto(totales_dia['neto'])}"
    )
    
    await query.edit_message_text(mensaje)

async def callback_cliente(query, data):
    """Registra ingreso de cliente"""
    _, monto = data.split(":")
    monto_float = float(monto)
    
    # Anti-duplicación por tiempo
    timestamp_actual = datetime.now()
    for m, t in ultimos_ingresos:
        if m == monto_float and (timestamp_actual - t).total_seconds() < 60:
            await query.edit_message_text("✅ Ese monto ya fue registrado recientemente")
            return
    
    hora_actual = timestamp_actual.strftime("%H:%M")
    
    sheets_manager.registrar_movimiento("cliente", monto_float, hora=hora_actual)
    ultimos_ingresos.append((monto_float, timestamp_actual))
    finance_service.invalidar_cache()
    
    totales_dia = finance_service.totales_dia()
    totales_mes = finance_service.totales_mes()
    
    mensaje = (
        f"✅ **INGRESO REGISTRADO**\n\n"
        f"💰 Monto: ${formatear_monto(monto_float)}\n"
        f"🕐 Hora: {hora_actual}\n\n"
        f"**HOY:**\n"
        f"💵 Clientes: ${formatear_monto(totales_dia['clientes'])}\n"
        f"📈 Total: ${formatear_monto(totales_dia['ingresos'])}\n\n"
        f"**MES:**\n"
        f"💰 Clientes: ${formatear_monto(totales_mes['clientes'])}\n"
        f"📊 Saldo: ${formatear_monto(totales_mes['neto'])}"
    )
    
    await query.edit_message_text(mensaje)

async def callback_consulta(query, data):
    """Maneja consultas de reportes"""
    tipo = data.split(":")[1]
    
    if tipo == "ingreso_hoy":
        totales = finance_service.totales_dia()
        mensaje = (
            f"📥 **INGRESOS DE HOY**\n\n"
            f"💰 Total: ${formatear_monto(totales['ingresos'])}\n"
            f"🧾 Clientes: ${formatear_monto(totales['clientes'])}\n"
            f"📊 Movimientos: {totales['cantidad_movimientos']}"
        )
    
    elif tipo == "egreso_hoy":
        totales = finance_service.totales_dia()
        mensaje = (
            f"📤 **EGRESOS DE HOY**\n\n"
            f"💸 Total: ${formatear_monto(abs(totales['egresos']))}"
        )
    
    elif tipo == "ingreso_mes":
        totales = finance_service.totales_mes()
        mensaje = (
            f"📆 **INGRESOS DEL MES**\n\n"
            f"💰 Total: ${formatear_monto(totales['ingresos'])}\n"
            f"🧾 Clientes: ${formatear_monto(totales['clientes'])}\n"
            f"📅 Días operativos: {totales['dias_operativos']}"
        )
    
    elif tipo == "egreso_mes":
        totales = finance_service.totales_mes()
        mensaje = (
            f"📉 **EGRESOS DEL MES**\n\n"
            f"💸 Total: ${formatear_monto(abs(totales['egresos']))}"
        )
    
    elif tipo == "saldo_mes":
        totales = finance_service.totales_mes()
        mensaje = (
            f"💰 **SALDO DEL MES**\n\n"
            f"💵 Ingresos: ${formatear_monto(totales['ingresos'])}\n"
            f"💸 Egresos: ${formatear_monto(abs(totales['egresos']))}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📊 **NETO: ${formatear_monto(totales['neto'])}**"
        )
    
    elif tipo == "estadisticas":
        stats = finance_service.estadisticas_avanzadas()
        
        if not stats:
            mensaje = "📊 No hay datos suficientes para estadísticas"
        else:
            proy = stats['proyeccion']
            mensaje = (
                f"📊 **ESTADÍSTICAS AVANZADAS**\n\n"
                f"💰 Promedio venta/día: ${formatear_monto(stats['promedio_venta_diaria'])}\n"
                f"🌟 Mejor día: {stats['mejor_dia']} (${formatear_monto(stats['mejor_dia_monto'])})\n"
                f"📅 Días operativos: {stats['dias_operativos']}\n\n"
                f"🔮 **PROYECCIÓN FIN DE MES:**\n"
                f"💵 Ingresos: ${formatear_monto(proy['ingresos'])}\n"
                f"💸 Egresos: ${formatear_monto(proy['egresos'])}\n"
                f"📈 Neto: ${formatear_monto(proy['neto'])}\n\n"
                f"💸 **TOP 5 GASTOS:**\n"
            )
            
            for prov, monto in stats['top_5_gastos'].items():
                mensaje += f"• {prov}: ${formatear_monto(monto)}\n"
    
    else:
        mensaje = "❓ Consulta no reconocida"
    
    await query.edit_message_text(mensaje)

async def callback_menu_pagar(query):
    """Muestra menú de egresos pendientes"""
    pendientes = finance_service.egresos_pendientes()
    
    if not pendientes:
        await query.edit_message_text("✅ No hay egresos pendientes de pago")
        return
    
    botones = []
    for p in pendientes:
        texto = f"{p['proveedor']} - ${formatear_monto(abs(p['monto']))} ({p['fecha']})"
        botones.append([
            InlineKeyboardButton(texto, callback_data=f"pagar_idx:{p['fila_idx']}")
        ])
    
    await query.edit_message_text(
        f"💸 **EGRESOS PENDIENTES** ({len(pendientes)})\n\n"
        "Seleccioná para marcar como pagado:",
        reply_markup=InlineKeyboardMarkup(botones)
    )

async def callback_confirmar_pago(query, data):
    """Marca un egreso como pagado"""
    fila_idx = int(data.split(":")[1])
    
    try:
        proveedor, monto = sheets_manager.marcar_como_pagado(fila_idx)
        finance_service.invalidar_cache()
        
        mensaje = (
            f"✅ **MARCADO COMO PAGADO**\n\n"
            f"📤 Proveedor: {proveedor}\n"
            f"💰 Monto: ${formatear_monto(abs(monto))}"
        )
        
        await query.edit_message_text(mensaje)
    
    except Exception as e:
        await query.edit_message_text(f"❌ Error al marcar como pagado: {e}")
