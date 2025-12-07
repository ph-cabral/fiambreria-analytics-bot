import time
from db_sheet import obtener_hoja_mes

def formatear_monto(monto):
    return format(float(monto), ",.2f").replace(",", "X").replace(".", ",").replace("X", ".")

def es_numero(valor):
    try:
        float(valor)
        return True
    except:
        return False

def obtener_hoja_segura(reintentos=3, espera=2):
    """Obtiene la hoja de cálculo con reintentos si falla."""
    for i in range(reintentos):
        try:
            return obtener_hoja_mes()
        except Exception as e:
            time.sleep(espera)
    raise Exception("No se pudo obtener la hoja después de varios intentos.")