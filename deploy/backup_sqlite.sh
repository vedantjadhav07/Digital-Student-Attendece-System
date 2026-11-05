#!/usr/bin/env bash
# Lab-Secure SQLite Safe WAL Backup Utility
# Uses SQLite's online vacuum into / .backup API to ensure zero write corruption during concurrent attendance.

set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/labsecure}"
DB_FILE="${APP_DIR}/instance/attendance.db"
BACKUP_DIR="${APP_DIR}/instance/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DEST="${BACKUP_DIR}/attendance_backup_${TIMESTAMP}.db"

mkdir -p "${BACKUP_DIR}"

if [ ! -f "${DB_FILE}" ]; then
    echo "Error: Database file ${DB_FILE} does not exist."
    exit 1
fi

echo "Initiating atomic snapshot of SQLite WAL database..."
# Use sqlite3 CLI .backup command to lock-safely duplicate WAL pages
sqlite3 "${DB_FILE}" ".backup '${BACKUP_DEST}'"

echo "Backup created successfully at: ${BACKUP_DEST}"

# Retain only last 30 backups to preserve disk space
find "${BACKUP_DIR}" -name "attendance_backup_*.db" -type f -mtime +30 -delete
echo "Old snapshots older than 30 days cleaned up."

