#!/usr/bin/env bash
#
# Restore an encrypted backup produced by ops/backup.sh.
#
#   ./ops/restore.sh backups/natstatevis-20260915-023000.sql.gz.enc
#
# This DESTROYS the current contents of the target database. It prompts for
# confirmation unless FORCE=1 is set.
#
# Verifying a restore is the only proof a backup works. Do one on the test
# environment before the cutover, not after.

set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_FILE="${1:-}"
if [[ -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <backup-file.sql.gz.enc>" >&2
    echo >&2
    echo "Available backups:" >&2
    ls -1t ./backups/*.sql.gz.enc 2>/dev/null | head -20 >&2 || echo "  (none)" >&2
    exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: $BACKUP_FILE not found." >&2
    exit 1
fi

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file ${ENV_FILE}"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${POSTGRES_USER:?POSTGRES_USER must be set}"
: "${POSTGRES_DB:?POSTGRES_DB must be set}"
: "${BACKUP_PASSPHRASE:?BACKUP_PASSPHRASE must be set in $ENV_FILE}"

echo "About to restore into database '${POSTGRES_DB}'."
echo "  Source:  ${BACKUP_FILE}"
echo "  This REPLACES all current data in that database."
if [[ "${FORCE:-0}" != "1" ]]; then
    read -r -p "Type the database name to confirm: " reply
    if [[ "$reply" != "$POSTGRES_DB" ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Stop the app first so no write lands mid-restore and no connection blocks the
# DROP statements in the dump.
echo ">>> Stopping the web container..."
$COMPOSE stop web

echo ">>> Restoring..."
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
    -pass env:BACKUP_PASSPHRASE \
    -in "$BACKUP_FILE" \
  | gunzip \
  | $COMPOSE exec -T db psql \
      -U "$POSTGRES_USER" \
      -d "$POSTGRES_DB" \
      -v ON_ERROR_STOP=1 \
      --quiet

echo ">>> Restarting the web container..."
$COMPOSE start web

# Ask Docker for the health status rather than curling through nginx. A plain
# http request to the host gets a 301 to https, which curl reports as success
# without ever reaching the application, so it proves nothing.
echo ">>> Waiting for the app to report healthy..."
for i in $(seq 1 30); do
    STATUS="$(docker inspect --format='{{.State.Health.Status}}' gclp_web 2>/dev/null || echo starting)"
    if [[ "$STATUS" == "healthy" ]]; then
        echo ">>> Restore complete, the app is healthy after $((i * 2))s."
        echo
        echo "    Verify the data landed:"
        echo "      $COMPOSE exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c 'SELECT count(*) FROM auth_user;'"
        exit 0
    fi
    sleep 2
done

echo ">>> Restore finished, but the container did not become healthy in 60s." >&2
echo "    Check: $COMPOSE logs --tail=50 web" >&2
exit 1
