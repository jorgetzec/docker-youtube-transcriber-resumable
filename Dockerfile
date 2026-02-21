FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para audio/video
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
# Instalar moviepy primero con sus dependencias
RUN pip install --no-cache-dir numpy pillow imageio imageio-ffmpeg decorator tqdm
RUN pip install --no-cache-dir -r requirements.txt

# Copiar scripts de Python
COPY transcriptor_cli_resumable.py .
COPY limpiar_archivos_temporales.py .
COPY test_transcriptor_cli_resumable.py .

# Crear directorio para salida
RUN mkdir -p /app/output

# Establecer punto de entrada
# ENTRYPOINT ["python"]

# No establecer ENTRYPOINT para permitir ejecutar comandos directamente
# El comando se especificará en docker-compose o al ejecutar el contenedor
