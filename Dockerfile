FROM python:3.10-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar archivos de requisitos primero (para cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear directorio para la base de datos si no existe
RUN mkdir -p db

# Variable de entorno para Python
ENV PYTHONUNBUFFERED=1

# Ejecutar el bot
CMD ["python", "main.py"]

