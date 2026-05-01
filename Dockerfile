# Etapa base con Python
FROM python:3.12-slim

# Establecer variable de entorno para Python
#Los mensajes de salida se mostrarán inmediatamente
ENV PYTHONUNBUFFERED=1   
# No se escribirán archivos .pyc, de cache de bytecode de Python, sirve para ahorrar espacio y evitar problemas de permisos en contenedores
ENV PYTHONDONTWRITEBYTECODE=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
# Actualiza e instala herramientas, el ultimo comando limpia la cache de apt para reducir el tamaño de la imagen

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar el proyecto
COPY . .

# Recolectar archivos estáticos (si usas)
RUN python manage.py collectstatic --noinput || true
# El comando anterior recolecta los archivos estáticos de tu proyecto Django. El flag --noinput evita que el comando solicite interacción, lo cual es importante en un entorno de contenedores. El || true al final asegura que el comando no falle si no hay archivos estáticos para recolectar, lo que puede ser útil durante el desarrollo o si tu proyecto no tiene archivos estáticos.

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]