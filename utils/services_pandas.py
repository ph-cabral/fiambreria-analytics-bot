# services_pandas.py
import pandas as pd
from datetime import datetime, timedelta
from functools import lru_cache
import time

class GestionFinanzas:
    def __init__(self, hoja_sheet):
        self.hoja = hoja_sheet
        self.cache_df = None
        self.cache_timestamp = None
        self.cache_duracion = 300  # 5 minutos
        
    def obtener_datos_mes(self, forzar=False):
        """Obtiene datos del mes usando caché inteligente"""
        ahora = time.time()
        
        if (not forzar and 
            self.cache_df is not None and 
            self.cache_timestamp and 
            (ahora - self.cache_timestamp) < self.cache_duracion):
            return self.cache_df.copy()
        
        # Obtener datos de Google Sheets
        datos = self.hoja.get_all_records()
        
        # Convertir a DataFrame de pandas
        df = pd.DataFrame(datos)
        
        # Limpieza y conversión de tipos
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce')
        df['Pagado'] = df['Pagado'].astype(str).str.lower() == 'true'
        
        # Agregar columnas calculadas
        df['Mes'] = df['Fecha'].dt.to_period('M')
        df['Dia'] = df['Fecha'].dt.date
        df['EsIngreso'] = df['Monto'] > 0
        df['EsEgreso'] = df['Monto'] < 0
        
        # Categorizar proveedores
        df['Categoria'] = df['Proveedor'].apply(self._categorizar_proveedor)
        
        # Actualizar caché
        self.cache_df = df.copy()
        self.cache_timestamp = ahora
        
        return df
    
    def _categorizar_proveedor(self, proveedor):
        """Categoriza proveedores para análisis"""
        categorias = {
            'Cliente': ['cliente'],
            'Gastos Propios': ['Nosotros'],
            'Mercadería': ['Mercaderia', 'Mercadería'],
            'Desperdicio': ['Desperdicio'],
            'Corrección': ['Corrección Caja'],
        }
        
        proveedor_lower = str(proveedor).lower()
        for categoria, palabras in categorias.items():
            if any(p.lower() in proveedor_lower for p in palabras):
                return categoria
        return 'Proveedor'
    
    def totales_dia(self, fecha=None):
        """Calcula totales del día con pandas"""
        if fecha is None:
            fecha = datetime.now().date()
        
        df = self.obtener_datos_mes()
        df_dia = df[df['Dia'] == fecha]
        
        return {
            'ingresos': df_dia[df_dia['EsIngreso']]['Monto'].sum(),
            'egresos': df_dia[df_dia['EsEgreso']]['Monto'].sum(),
            'neto': df_dia['Monto'].sum(),
            'clientes': df_dia[df_dia['Proveedor'] == 'cliente']['Monto'].sum(),
            'por_categoria': df_dia.groupby('Categoria')['Monto'].sum().to_dict()
        }
    
    def totales_mes(self, excluir_no_contables=True):
        """Calcula totales del mes"""
        df = self.obtener_datos_mes()
        mes_actual = datetime.now().replace(day=1).date()
        df_mes = df[df['Fecha'] >= pd.Timestamp(mes_actual)]
        
        if excluir_no_contables:
            df_mes = df_mes[~df_mes['Categoria'].isin(['Mercadería', 'Desperdicio'])]
        
        return {
            'ingresos': df_mes[df_mes['EsIngreso']]['Monto'].sum(),
            'egresos': df_mes[df_mes['EsEgreso']]['Monto'].sum(),
            'neto': df_mes['Monto'].sum(),
            'clientes': df_mes[df_mes['Proveedor'] == 'cliente']['Monto'].sum(),
            'por_proveedor': df_mes[df_mes['EsEgreso']].groupby('Proveedor')['Monto'].sum().to_dict()
        }
    
    def egresos_pendientes(self):
        """Obtiene egresos pendientes de pago"""
        df = self.obtener_datos_mes()
        pendientes = df[(df['EsEgreso']) & (~df['Pagado'])]
        
        return pendientes[['Proveedor', 'Monto', 'Fecha']].to_dict('records')
    
    def total_proveedor(self, proveedor, mes_actual=True):
        """Total pagado a un proveedor específico"""
        df = self.obtener_datos_mes()
        
        if mes_actual:
            mes = datetime.now().replace(day=1).date()
            df = df[df['Fecha'] >= pd.Timestamp(mes)]
        
        return df[df['Proveedor'] == proveedor]['Monto'].sum()
    
    def estadisticas_avanzadas(self):
        """Análisis avanzado para toma de decisiones"""
        df = self.obtener_datos_mes()
        mes_actual = datetime.now().replace(day=1).date()
        df_mes = df[df['Fecha'] >= pd.Timestamp(mes_actual)]
        
        return {
            'promedio_venta_diaria': df_mes[df_mes['Proveedor'] == 'cliente'].groupby('Dia')['Monto'].sum().mean(),
            'mejor_dia': df_mes[df_mes['Proveedor'] == 'cliente'].groupby('Dia')['Monto'].sum().idxmax(),
            'top_5_gastos': df_mes[df_mes['EsEgreso']].groupby('Proveedor')['Monto'].sum().nsmallest(5).to_dict(),
            'dias_operativos': df_mes['Dia'].nunique(),
            'proyeccion_mes': self._proyectar_mes(df_mes)
        }
    
    def _proyectar_mes(self, df_mes):
        """Proyecta ingresos/egresos para fin de mes"""
        dias_transcurridos = (datetime.now().date() - datetime.now().replace(day=1).date()).days
        dias_mes = 30  # simplificado
        
        if dias_transcurridos == 0:
            return None
        
        ingresos_actuales = df_mes[df_mes['EsIngreso']]['Monto'].sum()
        egresos_actuales = abs(df_mes[df_mes['EsEgreso']]['Monto'].sum())
        
        factor = dias_mes / dias_transcurridos
        
        return {
            'ingresos_proyectados': ingresos_actuales * factor,
            'egresos_proyectados': egresos_actuales * factor,
            'neto_proyectado': (ingresos_actuales - egresos_actuales) * factor
        }
            