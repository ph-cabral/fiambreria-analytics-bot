import time
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from collections import deque

from telegram_conect import teclado_proveedores
from db_sheet import (
    registrar_ingreso, 
    registrar_egreso, 
    eliminar_ultimo_cliente,
    obtener_datos_cache
)
from utils import formatear_monto, es_numero

procesados = set()
ultimos_ingresos = deque(maxlen=2)

_totales_globales = {
    "total_hoy": 0,
    "total_estado": 0,
    "ultima_actualizacion": 0
}

def obtener_totales_instantaneos():
    """Devuelve totales pre-calculados (instantáneo)"""
    ahora = time.time()
    
    if ahora - _totales_globales["ultima_actualizacion"] > 5:
        datos = obtener_datos_cache()
        hoy = datetime.now().date()
        excluir = {"Mercadería", "Desperdicio", "Mercaderia"}
        
        total_hoy = 0
        total_estado = 0
        
        for row in datos:
            monto_str = row.get("Monto", "")
            if not es_numero(monto_str):
                continue
            
            monto = float(monto_str)
            prov = row.get("Proveedor", "")
            fecha = row.get("Fecha", "")
            
            if prov == "cliente" and fecha:
                try:
                    if datetime.strptime(fecha, "%Y-%m-%d").date() == hoy:
                        total_hoy += monto
                except:
                    pass
            
            if prov not in excluir:
                total_estado += monto
        
        _totales_globales["total_hoy"] = total_hoy
        _totales_globales["total_estado"] = total_estado
        _totales_globales["ultima_actualizacion"] = ahora
    
    return _totales_globales

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = update.message.text.strip()

        if texto.replace(",", ".").replace(".", "", 1).isdigit():
            monto_float = float(texto.replace(",", "."))
            hora_actual = datetime.now().strftime("%H:%M")
            timestamp_actual = datetime.now()

            # Anti-duplicados
            for m, t in ultimos_ingresos:
                if m == monto_float and (timestamp_actual - t).total_seconds() < 120:
                    await update.message.reply_text("✅ Ya registrado")
                    return

            # Registrar
            registrar_ingreso(monto_float, hora=hora_actual)
            ultimos_ingresos.append((monto_float, timestamp_actual))

            # Obtener totales
            totales = obtener_totales_instantaneos()
            totales["total_hoy"] += monto_float
            totales["total_estado"] += monto_float

            mensaje = (
                f"💰 ${formatear_monto(monto_float)} ({hora_actual})\n"
                f"📆 Día: ${formatear_monto(totales['total_hoy'])}\n"
                f"💰 Estado: ${formatear_monto(totales['total_estado'])}"
            )

            # 🔥 BOTONES CON ELIMINAR
            botones = [
                [
                    InlineKeyboardButton("📤 Proveedor", callback_data=f"p:{monto_float}"),
                    InlineKeyboardButton("💸 Gasto", callback_data=f"g:{monto_float}")
                ],
                [
                    InlineKeyboardButton("🗑️ Eliminar", callback_data="eliminar")  # 🔥 NUEVO
                ]
            ]

            await update.message.reply_text(mensaje, reply_markup=InlineKeyboardMarkup(botones))
            return

    except Exception as e:
        print(f"❌ {e}")

async def manejar_boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        if query.id in procesados:
            return
        procesados.add(query.id)

        data = query.data
        
         # ELIMINAR
        if data == "eliminar":
            from db_sheet import eliminar_ultima_operacion
            
            proveedor, monto = eliminar_ultima_operacion()
            
            if proveedor:
                # Recalcular totales
                totales = obtener_totales_instantaneos()
                
                mensaje = (
                    f"🗑️ Eliminado: {proveedor} ${formatear_monto(abs(monto))}\n"
                    f"📆 Día: ${formatear_monto(totales['total_hoy'])}\n"
                    f"💰 Estado: ${formatear_monto(totales['total_estado'])}"
                )
                await query.edit_message_text(mensaje)
            else:
                await query.edit_message_text("⚠️ No hay nada para eliminar")
            return
        
        
        # PROVEEDOR
        if data.startswith("p:"): 
            _, monto = data.split(":")
            await query.edit_message_text("📤 Proveedor:", reply_markup=teclado_proveedores(float(monto)))
            return
        
        # GASTO
        if data.startswith("g:"):
            _, monto = data.split(":")
            m = float(monto)
            
            botones = [
                [InlineKeyboardButton("🍻 Nosotros", callback_data=f"N:{m}")],
                [InlineKeyboardButton("🧀 Mercadería", callback_data=f"M:{m}")],
                [InlineKeyboardButton("🗑️ Desperdicio", callback_data=f"D:{m}")],
                [InlineKeyboardButton("📦 Corrección", callback_data=f"C:{m}")]
            ]
            
            await query.edit_message_text(f"💸 ${formatear_monto(m)}:", reply_markup=InlineKeyboardMarkup(botones))
            return

        # PROVEEDOR
        if data.startswith("proveedor:"):
            _, proveedor, monto = data.split(":")
            monto = -abs(float(monto))
            hora = datetime.now().strftime("%H:%M")

            eliminar_ultimo_cliente()
            registrar_egreso(proveedor, monto, hora=hora)

            totales = obtener_totales_instantaneos()
            totales["total_estado"] += monto


            mensaje = (
                f"📤 {proveedor}: ${formatear_monto(abs(monto))} ({hora})\n"
                f"💰 Estado: ${formatear_monto(totales['total_estado'])}"
            )
            
            # 🔥 BOTÓN ELIMINAR
            botones = [[InlineKeyboardButton("🗑️ Eliminar", callback_data="eliminar")]]
            
            await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(botones))
            return
            # await query.edit_message_text(
            #     f"📤 {proveedor}: ${formatear_monto(abs(monto))} ({hora})\n"
            #     f"💰 Estado: ${formatear_monto(totales['total_estado'])}"
            # )
            # return

        # GASTOS PROPIOS / NOSOTROS
        if data.startswith("N:"):
            _, monto = data.split(":")
            monto = -abs(float(monto))
            hora = datetime.now().strftime("%H:%M")

            eliminar_ultimo_cliente()
            registrar_egreso("Nosotros", monto, hora=hora)

            totales = obtener_totales_instantaneos()
            totales["total_estado"] += monto

            mensaje = (
                f"💸 Nosotros: ${formatear_monto(abs(monto))} ({hora})\n"
                f"💰 Estado: ${formatear_monto(totales['total_estado'])}"
            )
            
            # 🔥 BOTÓN ELIMINAR
            botones = [[InlineKeyboardButton("🗑️ Eliminar", callback_data="eliminar")]]
            
            await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(botones))
            return
        
            # await query.edit_message_text(
            #     f"💸 Nosotros: ${formatear_monto(abs(monto))} ({hora})\n"
            #     f"💰 Estado: ${formatear_monto(totales['total_estado'])}"
            # )
            # return

        # MERCADERÍA
        if data.startswith("M:"):
            _, monto = data.split(":")
            monto = -abs(float(monto)) * 0.7
            hora = datetime.now().strftime("%H:%M")

            eliminar_ultimo_cliente()
            registrar_egreso("Mercaderia", monto, hora=hora)

            mensaje = f"🧀 ${formatear_monto(abs(monto))} ({hora})"
            
            # 🔥 BOTÓN ELIMINAR
            botones = [[InlineKeyboardButton("🗑️ Eliminar", callback_data="eliminar")]]
            
            await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(botones))
            return
            # await query.edit_message_text(f"🧀 ${formatear_monto(abs(monto))} ({hora})")
            # return

        # DESPERDICIO
        if data.startswith("D:"):
            _, monto = data.split(":")
            monto = -abs(float(monto)) * 0.7
            hora = datetime.now().strftime("%H:%M")

            eliminar_ultimo_cliente()
            registrar_egreso("Desperdicio", monto, hora=hora)

            await query.edit_message_text(f"🗑️ ${formatear_monto(abs(monto))} ({hora})")
            return

        # CORRECCIÓN DE CAJA
        if data.startswith("C:"):
            _, monto = data.split(":")
            botones = [
                [
                    InlineKeyboardButton("Sobra", callback_data=f"S:{monto}"),
                    InlineKeyboardButton("Falta", callback_data=f"F:{monto}")
                ]
            ]
            
            mensaje = f"🗑️ ${formatear_monto(abs(monto))} ({hora})"
            
            # 🔥 BOTÓN ELIMINAR
            botones = [[InlineKeyboardButton("🗑️ Eliminar", callback_data="eliminar")]]
            
            await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(botones))
            return
        
            # await query.edit_message_text("📦 ¿Sobra/Falta?", reply_markup=InlineKeyboardMarkup(botones))
            # return

        # SOBRA EN CAJA
        if data.startswith("S:"):
            _, monto = data.split(":")
            monto = abs(float(monto))
            hora = datetime.now().strftime("%H:%M")

            eliminar_ultimo_cliente()
            registrar_egreso("Corrección Caja", monto, hora=hora)

            mensaje = f"✅ Sobra: ${formatear_monto(monto)} ({hora})"
            
            # 🔥 BOTÓN ELIMINAR
            botones = [[InlineKeyboardButton("🗑️ Eliminar", callback_data="eliminar")]]
            
            await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(botones))
            return
        
            # await query.edit_message_text(f"✅ Sobra: ${formatear_monto(monto)} ({hora})")
            # return

        # FALTA EN CAJA
        if data.startswith("F:"):
            _, monto = data.split(":")
            monto = -abs(float(monto))
            hora = datetime.now().strftime("%H:%M")

            eliminar_ultimo_cliente()
            registrar_egreso("Corrección Caja", monto, hora=hora)

            mensaje = f"⚠️ Falta: ${formatear_monto(abs(monto))} ({hora})"
            
            # 🔥 BOTÓN ELIMINAR
            botones = [[InlineKeyboardButton("🗑️ Eliminar", callback_data="eliminar")]]
            
            await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(botones))
            return
        
            # await query.edit_message_text(f"⚠️ Falta: ${formatear_monto(abs(monto))} ({hora})")
            # return

    except Exception as e:
        print(f"❌ {e}")
