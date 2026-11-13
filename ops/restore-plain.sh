#!/usr/bin/env bash
#
# Restore an UNENCRYPTED .sql dump, such as the ones ops/migrate-from-render.sh
# writes during the cutover.
#
#   ./ops/restore-plain.sh backups/droplet-pre-import-20260915-023000.sql
#
# For the encrypted nightly backups, use ops/restore.sh instead.
#
# This DESTROYS the current contents of the target database.

set -euo pipefail

cd "$(dirname "$0")/.."

DUMP_FILE="${1:-}"
if [[ -z "$DUMP_FILE" ]]; then
    echo "Usage: $0 <dump-file.sql>" >&2
    echo >&2
    echo "Available plain dumps:" >&2
    ls -1t ./backups/*.sql 2>/dev/null | head -20 >&2 || echo "  (none)" >&2
    exit 1
fi

if [[ ! -f "$DUMP_FILE" ]]; then
    echo "ERROR: $DUMP_FILE not found." >&2
    exit 1
fi

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file ${ENV_FILE}"

# shellcheck source=ops/load-env.sh
. "$(dirname "$0")/load-env.sh"
load_env "$ENV_FILE"

: "${POSTGRES_USER:?POSTGRES_USER must be set}"
: "${POSTGRES_DB:?POSTGRES_DB must be set}"

echo "About to restore into database '${POSTGRES_DB}' from ${DUMP_FILE}."
echo "This REPLACES all current data in that database."
if [[ "${FORCE:-0}" != "1" ]]; then
    read -r -p "Type the database name to confirm: " reply
    if [[ "$reply" != "$POSTGRES_DB" ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo ">>> Stopping the web container..."
$COMPOSE stop web

echo ">>> Restoring..."
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -v ON_ERROR_STOP=1 --quiet < "$DUMP_FILE"

echo ">>> Restarting the web container..."
$COMPOSE start web

echo ">>> Restore complete. Check: $COMPOSE logs --tail=50 web"
