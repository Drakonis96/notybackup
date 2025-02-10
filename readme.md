# Notion CSV Backup

**Notion CSV Backup** es una aplicación web desarrollada en **Flask** que permite realizar copias de seguridad de datos de una base de datos de **Notion**. 
La aplicación consulta la **API de Notion**, transforma la información en registros y los exporta en formato **CSV**. Además, mantiene un historial de backups en un 
archivo **JSON** y permite programar copias de seguridad de forma automática mediante **APScheduler**.

## 🚀 Características

- ✅ **Consulta a la API de Notion**: Extrae datos de una base de datos usando la clave API configurada.
- ✅ **Exportación a CSV**: Transforma los datos obtenidos en registros y los guarda en archivos CSV dentro de `backup_folders/`.
- ✅ **Historial de backups**: Registra la fecha, nombre del archivo, formato y cantidad de registros en `data/backups_history.json`.
- ✅ **Programación de tareas**: Permite programar backups automáticos a intervalos regulares mediante **APScheduler**.
- ✅ **Interfaz Web**: Ofrece formularios para iniciar backups manuales o programados y para visualizar el historial.

---

## 📁 Estructura del Proyecto

```
notybackup/
│── css/                 # Estilos CSS
│── data/                # Almacenamiento del historial de backups
│   ├── backups_history.json
│── img/                 # Imágenes
│── static/              # Archivos estáticos (CSS, imágenes)
│   ├── css/
│   ├── img/
│── templates/           # Plantillas HTML
│── Dockerfile           # Configuración de Docker
│── LICENSE              # Archivo de licencia
│── app.py               # Aplicación principal en Flask
│── docker-compose.yml   # Configuración de Docker Compose
│── dockerignore.txt     # Reglas para ignorar archivos en Docker
│── index.html           # Página principal de la interfaz web
│── readme.md            # Documentación del proyecto
│── requirements.txt     # Dependencias necesarias
│── result.html          # Página de resultados
│── style.css            # Estilos adicionales
```

---

## ⚙️ Instalación y Configuración

### 🔹 Requisitos

- Python 3.8+
- Notion API Token
- Docker (opcional, para despliegue con contenedores)

### 🔹 Instalación Manual

1. Clona el repositorio:
   ```sh
   git clone https://github.com/drakonis96/notybackup.git
   cd notybackup
   ```
2. Instala las dependencias:
   ```sh
   pip install -r requirements.txt
   ```
3. Configura la clave API de Notion en un archivo `.env`:
   ```env
   NOTION_API_KEY=tu_clave_aqui
   DATABASE_ID=tu_database_id
   ```
4. Ejecuta la aplicación:
   ```sh
   python app.py
   ```

### 🔹 Usando Docker

1. Construye la imagen Docker:
   ```sh
   docker build -t notybackup .
   ```
2. Inicia el contenedor:
   ```sh
   docker run -d -p 5000:5000 --env-file .env notybackup
   ```

---

## 🛠 Uso

1. Accede a la interfaz web en `http://localhost:5000`
2. Usa los formularios para iniciar un backup manual o programar uno automático.
3. Descarga los archivos CSV desde la sección de historial de backups.

---

## 📝 Licencia

Este proyecto está licenciado bajo la **GPLv3**. Consulta el archivo `LICENSE` para más detalles.

---
**.
