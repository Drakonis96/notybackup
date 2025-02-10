import os
import csv
import json
import requests
import shutil
import secrets
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, redirect, url_for, flash, stream_with_context, Response
from flask_apscheduler import APScheduler
from dotenv import load_dotenv
import re

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_urlsafe(32))

class Config:
    SCHEDULER_API_ENABLED = True
    # Configuración adicional de APScheduler si la necesitas, por ejemplo:
    # SCHEDULER_JOB_DEFAULTS = {
    #     'coalesce': False,  # Evita ejecuciones múltiples si se pierde una
    #     'max_instances': 1   # Solo una instancia del backup a la vez
    # }

app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# --- Configuración de persistencia --- (sin cambios)
DATA_DIR = os.path.join(os.getcwd(), "data")
BACKUP_DIR = os.path.join(os.getcwd(), "backup_folders")

def set_permissions(path, uid, gid):
    try:
        os.chown(path, uid, gid)
    except OSError as e:
        print(f"Error al cambiar permisos de {path}: {e}")

def create_dir_if_not_exists(dir_path, uid=None, gid=None):
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            if uid is not None and gid is not None:
                set_permissions(dir_path, uid, gid)
        except OSError as e:
            print(f"Error al crear el directorio {dir_path}: {e}")

PUID = os.getenv('PUID')
PGID = os.getenv('PGID')
if PUID is not None and PGID is not None:
    PUID = int(PUID)
    PGID = int(PGID)

create_dir_if_not_exists(DATA_DIR, PUID, PGID)
create_dir_if_not_exists(BACKUP_DIR, PUID, PGID)

HISTORY_FILE = os.path.join(DATA_DIR, "backups_history.json")
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    if PUID is not None and PGID is not None:
        set_permissions(HISTORY_FILE, PUID, PGID)

DB_IDS_FILE = os.path.join(DATA_DIR, "database_ids.json")
if not os.path.exists(DB_IDS_FILE):
    with open(DB_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    if PUID is not None and PGID is not None:
        set_permissions(DB_IDS_FILE, PUID, PGID)

def load_database_ids():
    try:
        with open(DB_IDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_database_ids(ids_list):
    with open(DB_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(ids_list, f, ensure_ascii=False, indent=4)
    if PUID is not None and PGID is not None:
        set_permissions(DB_IDS_FILE, PUID, PGID)


# --- Funciones para manejar Notion (CORRECTED) ---
NOTION_API_URL = "https://api.notion.com/v1/databases/{}/query"
NOTION_VERSION = "2022-06-28"
PROPERTY_TYPE_MAP = {
    "title": lambda prop: "".join([item.get("plain_text", "") for item in prop.get("title", [])]),
    "rich_text": lambda prop: "".join([item.get("plain_text", "") for item in prop.get("rich_text", [])]),
    "number": lambda prop: str(prop.get("number")) if prop.get("number") is not None else "",
    "checkbox": lambda prop: str(prop.get("checkbox")),
    "date": lambda prop: prop.get("date", {}).get("start", "") if prop.get("date") else "",
    "select": lambda prop: prop.get("select", {}).get("name", "") if prop.get("select") else "",
    "multi_select": lambda prop: ", ".join([option.get("name", "") for option in prop.get("multi_select", [])]),
    "url": lambda prop: prop.get("url", ""),
    "email": lambda prop: prop.get("email", ""),
    "phone_number": lambda prop: prop.get("phone_number", ""),
    "formula": lambda prop: str(prop.get("formula", {}).get("string", "")),
    "relation": lambda prop: "",
    "rollup": lambda prop: "",
    "people": lambda prop: ", ".join([person.get("name", "") for person in prop.get("people", [])]),
    "files": lambda prop: ", ".join([file.get("name", "") for file in prop.get("files", [])]),
    "created_time": lambda prop: prop.get("created_time", ""),
    "last_edited_time": lambda prop: prop.get("last_edited_time", ""),
    "created_by": lambda prop: prop.get("created_by", {}).get("name", "") if prop.get("created_by") else "",
    "last_edited_by": lambda prop: prop.get("last_edited_by", {}).get("name", "") if prop.get("last_edited_by") else "",
}

def extract_property_value(prop):
    prop_type = prop.get("type")
    extractor = PROPERTY_TYPE_MAP.get(prop_type)
    return extractor(prop) if extractor else ""

def fetch_notion_data_in_batches(database_id, batch_size=100):
    """
    Fetches Notion data in batches (chunks), yielding each *batch* of results.
    This is a generator.
    """
    notion_key = os.getenv("NOTION_API_KEY")
    if not notion_key:
        raise ValueError("NOTION_API_KEY not set.")
    url = NOTION_API_URL.format(database_id)
    headers = {
        "Authorization": "Bearer " + notion_key,
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    payload = {}  # Start with an empty payload
    has_more = True
    next_cursor = None

    while has_more:
        if next_cursor:
            payload["start_cursor"] = next_cursor  # Add cursor if we have one
        try:
            # IMPORTANT: Use stream=True for streaming the response
            response = requests.post(url, headers=headers, json=payload, stream=True)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            # Process the response in chunks
            data = response.json() # Get the response as JSON
            results = data.get("results", [])
            yield results
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor", None)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error connecting to Notion: {e}")

def transform_to_records(batch):
    """
    Transforms a *batch* of Notion results into records.
    """
    records = []
    for result in batch:
        record = {}
        properties = result.get("properties", {})
        for key, prop in properties.items():
            record[key] = extract_property_value(prop)
        records.append(record)
    return records

def get_fieldnames_ordered(records):
    """
    Gets fieldnames (column names) in order, from a *batch* of records.
    Could be optimized to get fieldnames from a single Notion call,
    but this is clearer for this example.
    """
    fieldnames = []
    for record in records:
        for key in record.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    return fieldnames

def write_csv_in_batches(records_generator, file_name):
    """
    Writes a CSV in batches, using a generator of records.
    """
    file_name = re.sub(r'[\\/*?:"<>|]', "", file_name)
    if not file_name.endswith(".csv"):
        file_name += ".csv"
    file_path = os.path.join(BACKUP_DIR, file_name)

    # Handle duplicate filenames
    if os.path.exists(file_path):
        base, ext = os.path.splitext(file_name)
        counter = 1
        new_file_name = f"{base}_copia{counter}{ext}"
        new_file_path = os.path.join(BACKUP_DIR, new_file_name)
        while os.path.exists(new_file_path):
            counter += 1
            new_file_name = f"{base}_copia{counter}{ext}"
            new_file_path = os.path.join(BACKUP_DIR, new_file_name)
        file_name = new_file_name
        file_path = new_file_path

    try:
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = None  # Initialize writer outside the loop
            for records in records_generator:  # Iterate over *batches* of records
                if not records:  # Skip empty batches
                    continue

                if writer is None:  # First batch: create writer, write header
                    fieldnames = get_fieldnames_ordered(records)
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                for record in records:  # Iterate over records *within* the batch
                    writer.writerow(record)

        if PUID is not None and PGID is not None:
            set_permissions(file_path, PUID, PGID)
        return file_path

    except Exception as e:
        raise Exception(f"Error writing CSV: {e}")



def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(record):
    history = load_history()
    history.append(record)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)
    if PUID is not None and PGID is not None:
        set_permissions(HISTORY_FILE, PUID, PGID)

TZ = os.getenv("TZ", "UTC")

def run_backup(database_id, file_name):
    """
    Main backup function.  Now uses generators for batch processing.
    This function will be run in a background thread by APScheduler.
    """
    try:
        # Create a generator to fetch Notion data in batches
        notion_data_batches = fetch_notion_data_in_batches(database_id)

        # Create a generator to transform batches to records
        def records_generator():
            for batch in notion_data_batches:
                yield transform_to_records(batch)

        # Write the CSV using the records generator
        file_path = write_csv_in_batches(records_generator(), file_name)

        record_history = {
            "timestamp": datetime.now(ZoneInfo(TZ)).isoformat(),
            "file_name": os.path.basename(file_path),
            "format": "CSV",
            "num_records": "N/A"  # We *could* calculate this, but it's more complex with generators
        }
        save_history(record_history)
        return  # IMPORTANT:  No return value needed for background tasks

    except Exception as e:
        print(f"Error during backup: {e}")  # Log the error
        # Consider adding the error to the history, or notifying the user
        return  # No return value

# --- Flask routes (CORRECTED) ---

@app.route("/", methods=["GET", "POST"])
def index():
    history = load_history()
    db_ids = load_database_ids()

    if request.method == "POST":
        database_id = request.form.get("database_id", "").strip()
        file_name = request.form.get("file_name", "").strip()
        schedule_backup = request.form.get("schedule_backup", "off")

        database_id = re.sub(r'[^a-zA-Z0-9\-]', '', database_id)
        file_name = re.sub(r'[\\/*?:"<>|]', "", file_name)

        if not database_id or not file_name:
            flash("Please fill in all fields with valid values.")
            return redirect(url_for("index"))

        if schedule_backup == "on":
            schedule_type = request.form.get("schedule_type", "intervalo")
            job_id = "backup_job_" + uuid.uuid4().hex

            if schedule_type == "intervalo":
                interval_value = request.form.get("interval_value", "").strip()
                interval_unit = request.form.get("interval_unit", "minutes")

                if not interval_value.isdigit():
                    flash("Invalid interval. Must be a number.")
                    return redirect(url_for("index"))

                interval_value = int(interval_value)
                kwargs = {"seconds": 0, "minutes": 0, "hours": 0, "days": 0}
                if interval_unit == "seconds":
                    kwargs["seconds"] = interval_value
                elif interval_unit == "minutes":
                    kwargs["minutes"] = interval_value
                elif interval_unit == "hours":
                    kwargs["hours"] = interval_value
                elif interval_unit == "days":
                    kwargs["days"] = interval_value
                else:
                    flash("Invalid interval unit.")
                    return redirect(url_for("index"))

                scheduler.add_job(
                    id=job_id,
                    func=run_backup,
                    trigger="interval",
                    args=[database_id, file_name],
                    **kwargs
                )
                flash(f"Backup scheduled (ID: {job_id}) every {interval_value} {interval_unit}.")

            elif schedule_type == "cron":
                cron_weekday = request.form.get("cron_weekday", "").strip()
                cron_hour = request.form.get("cron_hour", "").strip()
                cron_minute = request.form.get("cron_minute", "").strip()

                if not (cron_weekday.isdigit() and cron_hour.isdigit() and cron_minute.isdigit()):
                    flash("Please enter valid numeric values for day of week, hour, and minute.")
                    return redirect(url_for("index"))

                cron_weekday, cron_hour, cron_minute = int(cron_weekday), int(cron_hour), int(cron_minute)
                if not (0 <= cron_weekday <= 6 and 0 <= cron_hour <= 23 and 0 <= cron_minute <= 59):
                    flash("Out-of-range values for cron.")
                    return redirect(url_for("index"))

                scheduler.add_job(
                    id=job_id,
                    func=run_backup,
                    trigger="cron",
                    args=[database_id, file_name],
                    day_of_week=str(cron_weekday),
                    hour=str(cron_hour),
                    minute=str(cron_minute)
                )
                flash(f"Backup scheduled (ID: {job_id}) weekly on day {cron_weekday} at {cron_hour:02d}:{cron_minute:02d}.")
            return redirect(url_for("index"))

        else:
            # --- CORRECTED: Immediate backup - Schedule for NOW ---
            job_id = "backup_immediate_" + uuid.uuid4().hex
            scheduler.add_job(
                id=job_id,
                func=run_backup,
                trigger="date",  # Single run, scheduled for...
                run_date=datetime.now(),  # ...NOW!
                args=[database_id, file_name]
            )
            flash("Backup initiated in the background. Check the history for the result.")  # User feedback
            return redirect(url_for("index")) # Redirect IMMEDIATELY

    scheduled_jobs = scheduler.get_jobs()
    return render_template("index.html", history=history, scheduled_jobs=scheduled_jobs, db_ids=db_ids)

# --- Other routes (no significant changes) ---

@app.route("/clear_history", methods=["POST"])
def clear_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        if PUID is not None and PGID is not None:
            set_permissions(HISTORY_FILE, PUID, PGID)
        flash("History cleared.")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect(url_for("index"))

@app.route("/delete_backups", methods=["POST"])
def delete_backups():
    try:
        if os.path.exists(BACKUP_DIR):
            for filename in os.listdir(BACKUP_DIR):
                file_path = os.path.join(BACKUP_DIR, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        flash("Backups deleted.")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect(url_for("index"))

@app.route("/delete_scheduled_backup/<job_id>", methods=["POST"])
def delete_scheduled_backup(job_id):
    try:
        scheduler.remove_job(job_id)
        flash(f"Scheduled backup {job_id} deleted.")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect(url_for("index"))

@app.route("/add_database_id", methods=["POST"])
def add_database_id():
    db_id = request.form.get("db_id", "").strip()
    if not db_id:
        return redirect(url_for("index"))  # Or flash an error
    db_ids = load_database_ids()
    if db_id not in db_ids:  # Avoid duplicates
        db_ids.append(db_id)
        save_database_ids(db_ids)
    return redirect(url_for("index"))

@app.route("/delete_database_id/<db_id>", methods=["POST"])
def delete_database_id(db_id):
    db_ids = load_database_ids()
    if db_id in db_ids:
        db_ids.remove(db_id)
        save_database_ids(db_ids)
    return redirect(url_for("index"))

@app.template_filter('local_time')
def local_time_filter(value):
    if value is None:
        return "N/A"
    return value.astimezone(ZoneInfo(TZ)).strftime("%Y-%m-%d %H:%M:%S")

@app.template_filter('format_datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return value  # Return original value if parse fails
    elif isinstance(value, datetime):
        dt = value
    else:
        return value
    return dt.strftime(format)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)