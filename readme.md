# Notybackup - Automated Notion CSV Backup

<img src="https://github.com/user-attachments/assets/6ad79f5c-c541-4a64-a81b-4dfdca52a221" alt="logo" width="100">

**Notion CSV Backup** is a web application developed in **Flask** that allows backing up data from a **Notion** database.  
The application queries the **Notion API**, transforms the information into records, and exports them in **CSV** format.  
Additionally, it maintains a backup history in a **JSON** file and enables scheduling automatic backups using **APScheduler**.

## 🚀 Features

- ✅ **Notion API Query**: Extracts data from a database using the configured API key.
- ✅ **CSV Export**: Converts retrieved data into records and saves them as CSV files in `backup_folders/`.
- ✅ **Backup History**: Logs the date, file name, format, and record count in `data/backups_history.json`.
- ✅ **Task Scheduling**: Enables automatic backup scheduling at regular intervals via **APScheduler**.
- ✅ **Web Interface**: Provides forms to initiate manual or scheduled backups and view the history.

---

## 📁 Project Structure

```
notybackup/
│── css/                 # CSS styles
│── data/                # Backup history storage
│   ├── backups_history.json
│── img/                 # Images
│── static/              # Static files (CSS, images)
│   ├── css/
│   ├── img/
│── templates/           # HTML templates
│── Dockerfile           # Docker configuration
│── LICENSE              # License file
│── app.py               # Main Flask application
│── docker-compose.yml   # Docker Compose configuration
│── dockerignore.txt     # Docker ignore rules
│── index.html           # Main web interface page
│── readme.md            # Project documentation
│── requirements.txt     # Required dependencies
│── result.html          # Results page
│── style.css            # Additional styles
```

---

## ⚙️ Installation & Setup

### 🔹 Requirements

- Python 3.8+
- Notion API Token
- Docker (optional, for containerized deployment)

### 🔹 Recommended Installation with Docker Compose

1. Create a `docker-compose.yml` file and add the following configuration:

   ```yaml
   version: "3.8"
   services:
     notion_backup:
       image: drakonis96/notybackup:latest
       ports:
         - "5005:5005"
       environment:
         - NOTION_API_KEY=your_notion_secret_key  # REPLACE!
         - FLASK_SECRET_KEY=a_random_long_secret_key  # REPLACE!
         - PUID=1000  # Replace with your UID
         - PGID=1000  # Replace with your GID
         - TZ=Europe/Madrid   # Replace with your TZ
       volumes:
         - /data/mynotionbackup/data:/app/data # Replace path
         - /data/mynotionbackup/backup_folders:/app/backup_folders   # Replace path
       restart: unless-stopped
   ```

2. Run the following command to start the service:

   ```sh
   docker-compose up -d
   ```

This will pull the latest version of **Notybackup**, start it as a background service, and automatically restart it if it crashes.

---

## 🛠 Usage

1. Access the web interface at `http://localhost:5005`
2. Use the forms to initiate a manual backup or schedule an automatic one.
3. Download CSV files from the backup history section.

---

## 📝 License

Este proyecto está licenciado bajo la **GPLv3**. Consulta el archivo `LICENSE` para más detalles.

---
**.
