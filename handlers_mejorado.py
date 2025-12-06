# handlers_mejorado.py
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from collections import deque

from utils.services_pandas import GestionFinanzas
from db_sheet import registrar_ingreso, registrar_egreso, obtener_hoja_mes
from utils import formatear_monto

# Instancia global del gestor
gestor = GestionFinanzas(obtener_hoja_mes())

procesados = set()
ultimos_ingresos = deque(maxlen=2)

async def manejar_boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        if query.id in procesados:
            return
        procesados.add(query.id)

        data = query.data
        
        # PAGO A PROVEEDOR
        if data.startswith("proveedor:"):
            _, proveedor, monto = data.split(":")
            monto = -abs(float(monto))
            hora_actual = datetime.now().strftime("%H:%M")

            # Registrar egreso
            registrar_egreso(proveedor, monto, hora=hora_actual)
            
            # Invalidar caché y obtener nuevos datos
            gestor.obtener_datos_mes(forzar=True)
            
            # Obtener totales calculados con pandas
            totales_dia = gestor.totales_dia()
            totales_mes = gestor.totales_mes()
            total_prov = abs(gestor.total_proveedor(proveedor))

            mensaje = (
                f"📤 Pago a {proveedor}: ${formatear_monto(abs(monto))} ({hora_actual})\n"
                f"📊 Total pagado a {proveedor} (mes): ${formatear_monto(total_prov)}\n"
                f"📆 Saldo del día: ${formatear_monto(totales_dia['neto'])}\n"
                f"📅 Saldo del mes: ${formatear_monto(totales_mes['neto'])}"
            )

            await query.edit_message_text(mensaje)
            return

        # INGRESO DE CLIENTE
        if data.startswith("cliente:"):
            _, monto = data.split(":")
            monto_float = float(monto)
            hora_actual = datetime.now().strftime("%H:%M")
            timestamp_actual = datetime.now()

            # Evitar duplicados
            for m, t in ultimos_ingresos:
                if m == monto_float and (timestamp_actual - t).total_seconds() < 120:
                    await query.edit_message_text("✅ Ya registré ese monto")
                    return

            registrar_ingreso(monto_float, hora=hora_actual)
            ultimos_ingresos.append((monto_float, timestamp_actual))

            # Actualizar datos
            gestor.obtener_datos_mes(forzar=True)
            totales_dia = gestor.totales_dia()
            totales_mes = gestor.totales_mes()

            mensaje = (
                f"💰 Ingreso: ${formatear_monto(monto_float)} ({hora_actual})\n"
                f"📆 Total del día: ${formatear_monto(totales_dia['clientes'])}\n"
                f"📊 Estado Mes: ${formatear_monto(totales_mes['neto'])}"
            )

            await query.edit_message_text(mensaje)
            return

        # CONSULTAS
        if data.startswith("consulta:"):
            tipo = data.split(":")[1]
            
            if tipo == "estadisticas":
                stats = gestor.estadisticas_avanzadas()
                proyeccion = stats['proyeccion_mes']
                
                mensaje = (
                    f"📊 **ESTADÍSTICAS AVANZADAS**\n\n"
                    f"💰 Promedio venta diaria: ${formatear_monto(stats['promedio_venta_diaria'])}\n"
                    f"🌟 Mejor día: {stats['mejor_dia']}\n"
                    f"📅 Días operativos: {stats['dias_operativos']}\n\n"
                    f"🔮 **PROYECCIÓN FIN DE MES:**\n"
                    f"Ingresos: ${formatear_monto(proyeccion['ingresos_proyectados'])}\n"
                    f"Egresos: ${formatear_monto(proyeccion['egresos_proyectados'])}\n"
                    f"Neto: ${formatear_monto(proyeccion['neto_proyectado'])}\n\n"
                    f"💸 **TOP 5 GASTOS:**\n"
                )
                
                for prov, monto in stats['top_5_gastos'].items():
                    mensaje += f"• {prov}: ${formatear_monto(abs(monto))}\n"
                
                await query.edit_message_text(mensaje)
                return

    except Exception as e:
        print(f"❌ Error: {e}")
        await query.edit_message_text("⚠️ Error al procesar")
