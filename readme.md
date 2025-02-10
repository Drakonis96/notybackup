#Notion CSV Backup

Notion CSV Backup is a web application developed in Flask that allows users to back up data from a Notion database. The application queries the Notion API, transforms the information into records, and exports them in CSV format. Additionally, it maintains a backup history in a JSON file and enables automatic backup scheduling using APScheduler.

##Features
✅ Query Notion API: Extracts data from a Notion database using a configured API key.
✅ CSV Export: Transforms the retrieved data into records and saves them as CSV files inside backup_folders/.
✅ Backup History: Logs the date, file name, format, and record count in data/backups_history.json.
✅ Task Scheduling: Enables automatic backup scheduling at regular intervals using APScheduler.
✅ Web Interface: Provides forms to start manual or scheduled backups and view the backup history.

##Project Structure

notybackup/
│── css/                 # Stylesheets
│── data/                # Backup history storage
│   ├── backups_history.json
│── img/                 # Image assets
│── static/              # Static files (CSS, images)
│   ├── css/
│   ├── img/
│── templates/           # HTML templates
│── Dockerfile           # Docker configuration
│── LICENSE              # License file
│── app.py               # Main Flask application
│── docker-compose.yml   # Docker Compose configuration
│── dockerignore.txt     # Docker ignore rules
│── index.html           # Web interface homepage
│── readme.md            # Documentation
│── requirements.txt     # Dependencies
│── result.html          # Result page template
│── style.css            # Additional styles
