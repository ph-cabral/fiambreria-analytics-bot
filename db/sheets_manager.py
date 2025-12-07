import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import time
from config import config

class SheetsManager:
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    def __init__(self):
        self.credenciales = Credentials.from_service_account_file(
            config.GOOGLE_CREDENTIALS_FILE, 
            scopes=self.SCOPES
        )
        self.cliente = gspread.authorize(self.credenciales)
        self.spreadsheet_name = config.SPREADSHEET_NAME
        self._hoja_cache = None
        self._cache_timestamp = None
        
    def obtener_hoja_mes(self, forzar=False):
        """Obtiene u crea la hoja del mes actual"""
        ahora = time.time()
        
        # Cache de la hoja por 60 segundos
        if (not forzar and 
            self._hoja_cache and 
            self._cache_timestamp and 
            (ahora - self._cache_timestamp) < 60):
            return self._hoja_cache
        
        try:
            sheet = self.cliente.open(self.spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            print(f"📝 Creando spreadsheet: {self.spreadsheet_name}")
            sheet = self.cliente.create(self.spreadsheet_name)
        
        mes = datetime.now().strftime("%Y-%m")
        
        try:
            hoja = sheet.worksheet(mes)
        except gspread.WorksheetNotFound:
            print(f"📄 Creando hoja para mes: {mes}")
            hoja = sheet.add_worksheet(title=mes, rows=1000, cols=5)
            hoja.append_row(["Fecha", "Hora", "Proveedor", "Monto", "Pagado"])
        
        self._hoja_cache = hoja
        self._cache_timestamp = ahora
        return hoja
    
    def obtener_datos_como_dataframe(self):
        """Obtiene todos los datos del mes como DataFrame de pandas"""
        hoja = self.obtener_hoja_mes()
        datos = hoja.get_all_records()
        
        if not datos:
            # DataFrame vacío con estructura correcta
            return pd.DataFrame(columns=['Fecha', 'Hora', 'Proveedor', 'Monto', 'Pagado'])
        
        df = pd.DataFrame(datos)
        
        # Conversión de tipos
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce')
        df['Pagado'] = df['Pagado'].astype(str).str.lower().isin(['true', '1', 'si', 'sí'])
        
        # Limpiar filas con errores
        df = df.dropna(subset=['Fecha', 'Monto'])
        
        return df
    
    def registrar_movimiento(self, proveedor, monto, hora=None, pagado=True):
        """Registra un movimiento (ingreso o egreso)"""
        ahora = datetime.now()
        hora_formateada = hora if hora else ahora.strftime("%H:%M")
        
        hoja = self.obtener_hoja_mes()
        
        fila = [
            ahora.strftime("%Y-%m-%d"),
            hora_formateada,
            proveedor,
            float(monto),
            str(pagado)
        ]
        
        hoja.append_row(fila)
        
        # Invalidar cache
        self._hoja_cache = None
        
        print(f"✅ Registrado: {proveedor} - ${monto}")
        return fila
    
    def marcar_como_pagado(self, fila_idx):
        """Marca un egreso como pagado"""
        hoja = self.obtener_hoja_mes()
        
        # Obtener datos de la fila
        fila_datos = hoja.row_values(fila_idx)
        
        if len(fila_datos) >= 5:
            proveedor = fila_datos[2]
            monto = float(fila_datos[3])
            
            # Actualizar columna Pagado
            hoja.update_cell(fila_idx, 5, "True")
            
            # Invalidar cache
            self._hoja_cache = None
            
            print(f"✅ Marcado como pagado: {proveedor} - ${monto}")
            return proveedor, monto
        
        raise ValueError("Fila no válida")
    
    def obtener_fila_por_indice(self, indice):
        """Obtiene una fila específica (para sistema de pago)"""
        hoja = self.obtener_hoja_mes()
        todas_filas = hoja.get_all_values()
        
        if 1 <= indice < len(todas_filas):
            return todas_filas[indice]
        return None
    
    def eliminar_ultimo_movimiento_cliente(self):
        """Elimina el último movimiento de Cliente (para correcciones)"""
        hoja = self.obtener_hoja_mes()
        todas_filas = hoja.get_all_values()
        
        # Buscar de abajo hacia arriba el último Cliente
        for i in range(len(todas_filas) - 1, 0, -1):
            if len(todas_filas[i]) >= 3 and todas_filas[i][2] == "Cliente":
                hoja.delete_rows(i + 1)  # +1 porque gspread usa índice 1-based
                self._hoja_cache = None
                print(f"🗑️ Eliminado ingreso de Cliente (fila {i+1})")
                return True
        
        return False
# Instancia global
sheets_manager = SheetsManager()
