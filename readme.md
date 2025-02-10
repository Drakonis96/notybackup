# Notion CSV Backup

Notion CSV Backup es una aplicación web desarrollada en Flask que permite realizar copias de seguridad de datos de una base de datos de Notion. La aplicación consulta la API de Notion, transforma la información en registros y los exporta en formato CSV. Además, mantiene un historial de backups en un archivo JSON y permite programar copias de seguridad de forma automática mediante APScheduler.

---

## Características

- **Consulta a la API de Notion:** Extrae datos de una base de datos usando la clave API configurada.
- **Exportación a CSV:** Transforma los datos obtenidos en registros y los guarda en archivos CSV dentro de `backup_folders/`.
- **Historial de backups:** Registra la fecha, nombre del archivo, formato y cantidad de registros en `data/backups_history.json`.
- **Programación de tareas:** Permite programar backups automáticos a intervalos regulares mediante APScheduler.
- **Interfaz Web:** Ofrece formularios para iniciar backups manuales o programados y para visualizar el historial.

---

## Estructura del Proyecto

