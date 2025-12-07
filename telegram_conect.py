from telegram import InlineKeyboardMarkup, InlineKeyboardButton

proveedores = [
    "Amiplast", "Anselmi",
    "Bachilito",
    "Cafaratti(pepsi)", "Chirola", "Coca",
    "Disbe", "Dussin", "Dutto", "DP(Paladini)", 
    "Empanadas", "Esperanza",
    "Fernando_Cavallo", "Freezo", 
    "Gastaldi", "Glass", "GrupoM",
    "Huevos",
    "La_Esquina", "L&L(Secco)", "La_Bri", "Las_Cañitas", 
    "Marzal", "Milanesas", "Moni(chocol/ensala)", 
    "Nono_Fidel", 
    "Panero", "Pauletto_rey", "Piamontesa", "Pizza_Juan", "Placeres_Naturales",
    "Region_Centro", 
    "Santa_Maria",
    "Veneziana", "Verduleria",
    "Otro"
]

def teclado_proveedores(monto):
    botones = []
    fila_temp = []

    # 🔹 Armar botones de proveedores en pares
    for proveedor in proveedores:
        fila_temp.append(
            InlineKeyboardButton(proveedor, callback_data=f"proveedor:{proveedor}:{monto}")
        )
        fila_temp.append(
            InlineKeyboardButton("⏳ A pagar", callback_data=f"apagar:{proveedor}:{monto}")
        )

        # Cuando ya hay 2 (Proveedor | Pagar), agregamos la fila
        botones.append(fila_temp)
        fila_temp = []
        
    return InlineKeyboardMarkup(botones)


def mostrar_consultas():                              
    botones = [
        [InlineKeyboardButton("📥 Ingreso hoy", callback_data="consulta:ingreso_hoy")],                             [InlineKeyboardButton("📤 Egreso hoy", callback_data="consulta:egreso_hoy")],
        [InlineKeyboardButton("📆 Ingreso mes", callback_data="consulta:ingreso_mes")],                             [InlineKeyboardButton("📉 Egreso mes", callback_data="consulta:egreso_mes")],
        [InlineKeyboardButton("💰 Saldo mes", callback_data="consulta:saldo_mes")],                                 [InlineKeyboardButton("💸 Pagar", callback_data="menu:pagar")]  # 👈 NUEVO
 ]
    return InlineKeyboardMarkup(botones)