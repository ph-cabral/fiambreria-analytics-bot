def formatear_monto(monto):
    """Formatea monto con separadores argentinos"""
    try:
        numero = float(monto)
        return format(abs(numero), ",.2f").replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

def es_numero(valor):
    """Verifica si un valor es numérico"""
    try:
        float(str(valor).replace(",", "."))
        return True
    except:
        return False
