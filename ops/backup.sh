#!/usr/bin/env bash
#
# Encrypted nightly database backup.
#
#   ./ops/backup.sh
#
# Writes ./backups/natstatevis-YYYYmmdd-HHMMSS.sql.gz.enc, encrypted with
# AES-256 using BACKUP_PASSPHRASE from .env.production, then deletes dumps older
# than BACKUP_RETENTION_DAYS.
#
# This satisfies the "encrypted backups with a defined retention period" item on
# the Temple vendor security questionnaire. Restore with ops/restore.sh.
#
# Install as a cron job on the Droplet (02:30 daily):
#   (crontab -l 2>/dev/null; echo "30 2 * * * cd /opt/globalcyberlawproject-ilit && ./ops/backup.sh >> /var/log/gclp-backup.log 2>&1") | crontab -
#
# The passphrase must also be stored off this Droplet. A backup encrypted with a
# key that only exists on the machine being backed up is not a backup.

set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file ${ENV_FILE}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

# shellcheck source=ops/load-env.sh
. "$(dirname "$0")/load-env.sh"
load_env "$ENV_FILE"

: "${POSTGRES_USER:?POSTGRES_USER must be set}"
: "${POSTGRES_DB:?POSTGRES_DB must be set}"
: "${BACKUP_PASSPHRASE:?BACKUP_PASSPHRASE must be set in $ENV_FILE}"

RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
OUTFILE="${BACKUP_DIR}/${POSTGRES_DB}-${TIMESTAMP}.sql.gz.enc"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

echo "[$(date -u +%FT%TZ)] Dumping ${POSTGRES_DB}..."

# pg_dump streams to stdout, gzip compresses, openssl encrypts. Nothing is ever
# written to disk in the clear. pipefail makes a failure anywhere fail the run.
$COMPOSE exec -T db pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
  | gzip -9 \
  | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
      -pass env:BACKUP_PASSPHRASE \
      -out "$OUTFILE" || PIPE_STATUS=$?

# With `set -e` and pipefail, a failure anywhere in that pipeline would abort
# the script before the checks below, leaving a truncated and world-readable
# file that still looks like a valid backup. Tighten permissions, then judge.
chmod 600 "$OUTFILE" 2>/dev/null || true

if [[ -n "${PIPE_STATUS:-}" ]]; then
    echo "[$(date -u +%FT%TZ)] ERROR: dump pipeline failed (${PIPE_STATUS})." >&2
    rm -f "$OUTFILE"
    exit 1
fi
SIZE="$(du -h "$OUTFILE" | cut -f1)"

# A dump of an empty or failed database is a few hundred bytes. Catch that here
# rather than discovering it during a restore.
BYTES="$(stat -c %s "$OUTFILE")"
if [[ "$BYTES" -lt 1024 ]]; then
    echo "[$(date -u +%FT%TZ)] ERROR: backup is only ${BYTES} bytes. Check the database." >&2
    exit 1
fi

echo "[$(date -u +%FT%TZ)] Wrote ${OUTFILE} (${SIZE})"

echo "[$(date -u +%FT%TZ)] Pruning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "${POSTGRES_DB}-*.sql.gz.enc" -type f \
    -mtime "+${RETENTION_DAYS}" -print -delete

REMAINING="$(find "$BACKUP_DIR" -name "${POSTGRES_DB}-*.sql.gz.enc" -type f | wc -l)"
echo "[$(date -u +%FT%TZ)] Done. ${REMAINING} backup(s) retained."
