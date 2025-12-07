import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
import threading
from queue import Queue

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credenciales = Credentials.from_service_account_file("credential.json", scopes=SCOPES)
cliente = gspread.authorize(credenciales)
SPREADSHEET_NAME = "Registro_Movimientos"

_cache = {
    "hoja": None,
    "mes": None,
    "datos": [],
    "timestamp": 0,
    "ttl": 15  # 15 segundos de cache
}

# COLA DE ESCRITURA ASÍNCRONA
_cola_escritura = Queue()
_escritor_activo = False

def _procesar_cola_escritura():
    """Hilo que procesa escrituras en background"""
    global _escritor_activo
    _escritor_activo = True
    
    while True:
        try:
            operacion = _cola_escritura.get(timeout=1)
            if operacion is None:  # Señal de parada
                break
            
            tipo, datos = operacion
            hoja = obtener_hoja_mes()
            
            if tipo == "append":
                hoja.append_row(datos)
            elif tipo == "delete":
                hoja.delete_rows(datos)
            elif tipo == "update":
                fila, col, valor = datos
                hoja.update_cell(fila, col, valor)
            
            time.sleep(0.1)  # Evitar rate limits
            
        except:
            continue
    
    _escritor_activo = False

_hilo_escritor = threading.Thread(target=_procesar_cola_escritura, daemon=True)
_hilo_escritor.start()

def obtener_hoja_mes():
    """Cache de hoja"""
    mes_actual = datetime.now().strftime("%Y-%m")
    
    if _cache["hoja"] and _cache["mes"] == mes_actual:
        return _cache["hoja"]
    
    try:
        sheet = cliente.open(SPREADSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sheet = cliente.create(SPREADSHEET_NAME)

    try:
        hoja = sheet.worksheet(mes_actual)
    except gspread.WorksheetNotFound:
        hoja = sheet.add_worksheet(title=mes_actual, rows="1000", cols="5")
        hoja.append_row(["Fecha", "Hora", "Proveedor", "Monto", "Pagado"])
    
    _cache["hoja"] = hoja
    _cache["mes"] = mes_actual
    return hoja

def obtener_datos_cache():
    """Cache de datos con TTL"""
    ahora = time.time()
    
    if (_cache["datos"] and 
        _cache["mes"] == datetime.now().strftime("%Y-%m") and
        (ahora - _cache["timestamp"]) < _cache["ttl"]):
        return _cache["datos"]
    
    hoja = obtener_hoja_mes()
    _cache["datos"] = hoja.get_all_records()
    _cache["timestamp"] = ahora
    return _cache["datos"]

def invalidar_cache():
    """Invalida cache inmediatamente"""
    _cache["timestamp"] = 0

def registrar_ingreso(monto, hora=None):
    """Escritura asíncrona"""
    ahora = datetime.now()
    hora_formateada = hora if hora else ahora.strftime("%H:%M")
    
    fila = [ahora.strftime("%Y-%m-%d"), hora_formateada, "cliente", monto, "True"]
    
    # Agregar a cache local INMEDIATAMENTE
    _cache["datos"].append({
        "Fecha": fila[0],
        "Hora": fila[1],
        "Proveedor": fila[2],
        "Monto": fila[3],
        "Pagado": fila[4]
    })
    
    # Enviar a cola de escritura
    _cola_escritura.put(("append", fila))

def registrar_egreso(proveedor, monto, hora=None, pagado=True):
    """Escritura asíncrona"""
    ahora = datetime.now()
    hora_formateada = hora if hora else ahora.strftime("%H:%M")
    
    fila = [ahora.strftime("%Y-%m-%d"), hora_formateada, proveedor, monto, str(pagado)]
    
    # Agregar a cache local INMEDIATAMENTE
    _cache["datos"].append({
        "Fecha": fila[0],
        "Hora": fila[1],
        "Proveedor": fila[2],
        "Monto": fila[3],
        "Pagado": fila[4]
    })
    
    # Enviar a cola
    _cola_escritura.put(("append", fila))

def eliminar_ultimo_cliente():
    """Elimina el último cliente (asíncrono)"""
    try:
        datos = _cache["datos"]
        
        for idx in range(len(datos) - 1, -1, -1):
            if datos[idx].get("Proveedor") == "cliente":
                fila_numero = idx + 2
                
                # Eliminar del cache INMEDIATAMENTE
                _cache["datos"].pop(idx)
                
                # Enviar a cola
                _cola_escritura.put(("delete", fila_numero))
                return True
        
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def eliminar_ultima_operacion():
    """Elimina la última fila registrada (cualquier tipo)"""
    try:
        hoja = obtener_hoja_mes()
        datos = hoja.get_all_records()
        
        if len(datos) == 0:
            return None, None
        
        # Obtener última fila
        ultima_fila = datos[-1]
        proveedor = ultima_fila.get("Proveedor", "")
        monto = ultima_fila.get("Monto", "0")
        
        # Eliminar última fila (datos + 2 porque: 1 header + 1 índice base-0)
        fila_numero = len(datos) + 1
        hoja.delete_rows(fila_numero)
        
        # 🔥 Eliminar del cache también
        if _cache["datos"]:
            _cache["datos"].pop()
        
        # print(f"✅ Eliminada última fila: {proveedor} - {monto}")
        return proveedor, float(monto)
    
    except Exception as e:
        print(f"❌ Error al eliminar: {e}")
        return None, None
