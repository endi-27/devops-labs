#!/bin/sh
set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "[$(date)] Starting PostgreSQL backup for microservices..."
mkdir -p "${BACKUP_DIR}"

DATABASES="${POSTGRES_MULTIPLE_DATABASES:-users_db,products_db,orders_db}"

for DB in $(echo "$DATABASES" | tr ',' ' '); do
    BACKUP_FILE="${BACKUP_DIR}/${DB}_backup_${TIMESTAMP}.sql.gz"
    echo "[$(date)] Backing up database ${DB} -> ${BACKUP_FILE}..."
    PGPASSWORD="${APP_CONFIG__DB__PASSWORD:-devops_secret_password}" \
    pg_dump -h "${APP_CONFIG__DB__HOST:-postgres}" \
            -U "${APP_CONFIG__DB__USER:-devops_user}" \
            -d "${DB}" \
            | gzip > "${BACKUP_FILE}"
done

echo "[$(date)] Microservices databases backup completed successfully."

# Retention: Keep only the 5 most recent backups per DB
echo "[$(date)] Cleaning up older backups, keeping only the 5 most recent per DB..."
for DB in $(echo "$DATABASES" | tr ',' ' '); do
    ls -1t "${BACKUP_DIR}/${DB}_backup_"*.sql.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
done
echo "[$(date)] Backup rotation completed."
