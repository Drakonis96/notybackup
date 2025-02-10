# Dockerfile
FROM python:3.12-slim
WORKDIR /app

# Instalar tzdata para disponer de la información de zonas horarias
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Exponer el puerto 5005
EXPOSE 5005

# Ejecutar la aplicación usando Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5005", "app:app"]
