# notificaciones.py
from datetime import datetime, time
from telegram import Bot
import asyncio

class SistemaNotificaciones:
    def __init__(self, bot_token, chat_id, gestor_finanzas):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.gestor = gestor_finanzas
    
    async def notificacion_diaria(self):
        """Resumen diario automático"""
        totales = self.gestor.totales_dia()
        
        mensaje = (
            f"📊 **RESUMEN DEL DÍA** - {datetime.now().strftime('%d/%m/%Y')}\n\n"
            f"💰 Ingresos: ${formatear_monto(totales['ingresos'])}\n"
            f"💸 Egresos: ${formatear_monto(abs(totales['egresos']))}\n"
            f"📈 Neto: ${formatear_monto(totales['neto'])}\n"
        )
        
        await self.bot.send_message(chat_id=self.chat_id, text=mensaje)
    
    async def alertas_pendientes(self):
        """Alerta de egresos pendientes de pago"""
        pendientes = self.gestor.egresos_pendientes()
        
        if len(pendientes) > 5:
            total_pendiente = sum(abs(p['Monto']) for p in pendientes)
            mensaje = (
                f"⚠️ **ALERTA: {len(pendientes)} PAGOS PENDIENTES**\n\n"
                f"Total a pagar: ${formatear_monto(total_pendiente)}\n\n"
                f"Recordá marcarlos como pagados cuando los hagas."
            )
            await self.bot.send_message(chat_id=self.chat_id, text=mensaje)
    
    async def proyeccion_semanal(self):
        """Proyección de cierre de mes"""
        stats = self.gestor.estadisticas_avanzadas()
        proy = stats['proyeccion_mes']
        
        mensaje = (
            f"🔮 **PROYECCIÓN FIN DE MES**\n\n"
            f"Ingresos estimados: ${formatear_monto(proy['ingresos_proyectados'])}\n"
            f"Egresos estimados: ${formatear_monto(proy['egresos_proyectados'])}\n"
            f"Resultado neto estimado: ${formatear_monto(proy['neto_proyectado'])}"
        )
        
        await self.bot.send_message(chat_id=self.chat_id, text=mensaje)
