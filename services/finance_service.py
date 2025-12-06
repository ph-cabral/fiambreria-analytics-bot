import pandas as pd
from datetime import datetime, timedelta
import time
from db.sheets_manager import sheets_manager
from config import config

class FinanceService:
    def __init__(self):
        self.sheets = sheets_manager
        self._cache_df = None
        self._cache_timestamp = None
        self._cache_duration = config.CACHE_DURATION
    
    def obtener_datos(self, forzar=False):
        """Obtiene datos con sistema de caché"""
        ahora = time.time()
        
        if (not forzar and 
            self._cache_df is not None and 
            self._cache_timestamp and 
            (ahora - self._cache_timestamp) < self._cache_duration):
            return self._cache_df.copy()
        
        df = self.sheets.obtener_datos_como_dataframe()
        
        # Agregar columnas calculadas
        if not df.empty:
            df['Dia'] = df['Fecha'].dt.date
            df['Mes'] = df['Fecha'].dt.to_period('M')
            df['EsIngreso'] = df['Monto'] > 0
            df['EsEgreso'] = df['Monto'] < 0
            df['MontoAbs'] = df['Monto'].abs()
        
        self._cache_df = df.copy()
        self._cache_timestamp = ahora
        
        return df
    
    def invalidar_cache(self):
        """Fuerza actualización de datos"""
        self._cache_df = None
        self._cache_timestamp = None
    
    def totales_dia(self, fecha=None):
        """Calcula totales del día"""
        if fecha is None:
            fecha = datetime.now().date()
        
        df = self.obtener_datos()
        
        if df.empty:
            return {
                'ingresos': 0,
                'egresos': 0,
                'neto': 0,
                'clientes': 0,
                'cantidad_movimientos': 0
            }
        
        df_dia = df[df['Dia'] == fecha]
        
        ingresos = df_dia[df_dia['EsIngreso']]['Monto'].sum()
        egresos = df_dia[df_dia['EsEgreso']]['Monto'].sum()
        clientes = df_dia[df_dia['Proveedor'].str.lower() == 'cliente']['Monto'].sum()
        
        return {
            'ingresos': float(ingresos),
            'egresos': float(egresos),
            'neto': float(ingresos + egresos),
            'clientes': float(clientes),
            'cantidad_movimientos': len(df_dia)
        }
    
    def totales_mes(self, excluir_categorias=None):
        """Calcula totales del mes"""
        df = self.obtener_datos()
        
        if df.empty:
            return {
                'ingresos': 0,
                'egresos': 0,
                'neto': 0,
                'clientes': 0,
                'dias_operativos': 0
            }
        
        # Filtrar solo el mes actual
        mes_actual = datetime.now().replace(day=1).date()
        df_mes = df[df['Fecha'] >= pd.Timestamp(mes_actual)]
        
        # Excluir categorías si se especifica
        if excluir_categorias:
            for cat in excluir_categorias:
                df_mes = df_mes[~df_mes['Proveedor'].str.contains(cat, case=False, na=False)]
        
        ingresos = df_mes[df_mes['EsIngreso']]['Monto'].sum()
        egresos = df_mes[df_mes['EsEgreso']]['Monto'].sum()
        clientes = df_mes[df_mes['Proveedor'].str.lower() == 'cliente']['Monto'].sum()
        
        return {
            'ingresos': float(ingresos),
            'egresos': float(egresos),
            'neto': float(ingresos + egresos),
            'clientes': float(clientes),
            'dias_operativos': df_mes['Dia'].nunique()
        }
    
    def total_proveedor(self, proveedor, solo_mes_actual=True):
        """Calcula total pagado a un proveedor"""
        df = self.obtener_datos()
        
        if df.empty:
            return 0
        
        if solo_mes_actual:
            mes_actual = datetime.now().replace(day=1).date()
            df = df[df['Fecha'] >= pd.Timestamp(mes_actual)]
        
        total = df[df['Proveedor'] == proveedor]['Monto'].sum()
        return float(total)
    
    def egresos_pendientes(self):
        """Obtiene lista de egresos no pagados"""
        df = self.obtener_datos()
        
        if df.empty:
            return []
        
        pendientes = df[(df['EsEgreso']) & (~df['Pagado'])].copy()
        
        if pendientes.empty:
            return []
        
        # Agregar índice de fila real (+ 2 por encabezado y base 1)
        pendientes['fila_idx'] = range(2, 2 + len(pendientes))
        
        resultado = []
        for _, row in pendientes.iterrows():
            resultado.append({
                'fila_idx': row['fila_idx'],
                'proveedor': row['Proveedor'],
                'monto': float(row['Monto']),
                'fecha': row['Fecha'].strftime('%d/%m/%Y'),
                'hora': row['Hora']
            })
        
        return resultado
    
    def estadisticas_avanzadas(self):
        """Análisis avanzado con pandas"""
        df = self.obtener_datos()
        
        if df.empty:
            return None
        
        mes_actual = datetime.now().replace(day=1).date()
        df_mes = df[df['Fecha'] >= pd.Timestamp(mes_actual)]
        
        # Ventas por día
        ventas_dia = df_mes[df_mes['Proveedor'].str.lower() == 'cliente'].groupby('Dia')['Monto'].sum()
        
        # Top gastos
        top_gastos = df_mes[df_mes['EsEgreso']].groupby('Proveedor')['MontoAbs'].sum().nlargest(5)
        
        # Proyección
        dias_transcurridos = (datetime.now().date() - mes_actual).days + 1
        dias_mes = 30
        
        ingresos_actuales = df_mes[df_mes['EsIngreso']]['Monto'].sum()
        egresos_actuales = df_mes[df_mes['EsEgreso']]['MontoAbs'].sum()
        
        factor = dias_mes / dias_transcurridos if dias_transcurridos > 0 else 1
        
        return {
            'promedio_venta_diaria': float(ventas_dia.mean()) if not ventas_dia.empty else 0,
            'mejor_dia': ventas_dia.idxmax().strftime('%d/%m') if not ventas_dia.empty else 'N/A',
            'mejor_dia_monto': float(ventas_dia.max()) if not ventas_dia.empty else 0,
            'top_5_gastos': {k: float(v) for k, v in top_gastos.items()},
            'dias_operativos': df_mes['Dia'].nunique(),
            'proyeccion': {
                'ingresos': float(ingresos_actuales * factor),
                'egresos': float(egresos_actuales * factor),
                'neto': float((ingresos_actuales - egresos_actuales) * factor)
            }
        }

# Instancia global
finance_service = FinanceService()
