#!/bin/sh
set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting PostgreSQL backup to ${BACKUP_FILE}..."
mkdir -p "${BACKUP_DIR}"

PGPASSWORD="${APP_CONFIG__DB__PASSWORD:-devops_secret_password}" \
pg_dump -h "${APP_CONFIG__DB__HOST:-postgres}" \
        -U "${APP_CONFIG__DB__USER:-devops_user}" \
        -d "${APP_CONFIG__DB__NAME:-devops_db}" \
        | gzip > "${BACKUP_FILE}"

echo "[$(date)] Backup completed successfully: ${BACKUP_FILE}"

# Retention: Keep only the 5 most recent backups
echo "[$(date)] Cleaning up older backups, keeping only the 5 most recent..."
ls -1t "${BACKUP_DIR}"/db_backup_*.sql.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
echo "[$(date)] Backup rotation completed."
