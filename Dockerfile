# Usar Python 3.11 slim para menor tamaño
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Variable de entorno para Python (evitar .pyc y buffer)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Comando para ejecutar el bot
CMD ["python", "main.py"]
