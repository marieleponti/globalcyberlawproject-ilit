#!/usr/bin/env bash
#
# Move the live database from Render's managed Postgres into the Droplet's
# Postgres container. This is Plan A, step 4 of the cutover plan.
#
#   RENDER_DATABASE_URL='postgresql://user:pass@host/db' ./ops/migrate-from-render.sh
#
# The research dataset is CSV files in the repository, so the only things that
# travel here are user accounts and sessions. That keeps the dump small and the
# window short, but it also means this step is easy to forget: `git pull` does
# NOT bring the database across.
#
# Run this as close to the DNS change as possible. Everything a user does on
# Render between this dump and the DNS switch is lost. That gap is the recovery
# point objective, and shrinking it is the whole point of running this last.
#
# Use the External Database URL from the Render dashboard, not the internal one.

set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file ${ENV_FILE}"
DUMP_DIR="${DUMP_DIR:-./backups}"

: "${RENDER_DATABASE_URL:?Set RENDER_DATABASE_URL to the External Database URL from the Render dashboard}"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${POSTGRES_USER:?POSTGRES_USER must be set}"
: "${POSTGRES_DB:?POSTGRES_DB must be set}"

TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
DUMP_FILE="${DUMP_DIR}/render-cutover-${TIMESTAMP}.sql"

mkdir -p "$DUMP_DIR"
chmod 700 "$DUMP_DIR"

echo "=============================================================="
echo " Render to Droplet database migration"
echo " Started: $(date -u +%FT%TZ)"
echo "=============================================================="
echo
echo "Before continuing, confirm that writes to Render have stopped."
echo "Anything written there after this dump will not come across."
if [[ "${FORCE:-0}" != "1" ]]; then
    read -r -p "Continue? [y/N] " reply
    [[ "$reply" == "y" || "$reply" == "Y" ]] || exit 1
fi

# --- 1. Dump ---------------------------------------------------------------
# pg_dump runs inside the web container, which has postgresql-client installed,
# so no client is needed on the Droplet host itself.
echo
echo ">>> [1/4] Dumping the Render database..."
$COMPOSE run --rm -T \
    -e PGSSLMODE=require \
    -e RENDER_DATABASE_URL="$RENDER_DATABASE_URL" \
    --entrypoint sh web \
    -c 'pg_dump --no-owner --no-privileges --clean --if-exists "$RENDER_DATABASE_URL"' \
    > "$DUMP_FILE"

chmod 600 "$DUMP_FILE"
BYTES="$(stat -c %s "$DUMP_FILE")"
if [[ "$BYTES" -lt 1024 ]]; then
    echo "ERROR: the dump is only ${BYTES} bytes. Check RENDER_DATABASE_URL." >&2
    exit 1
fi
echo "    Wrote ${DUMP_FILE} ($(du -h "$DUMP_FILE" | cut -f1))"

# --- 2. Snapshot the target ------------------------------------------------
# Taken before the import, so a botched load can be rolled back without going
# back to Render a second time.
echo
echo ">>> [2/4] Snapshotting the current Droplet database first..."
SAFETY_FILE="${DUMP_DIR}/droplet-pre-import-${TIMESTAMP}.sql"
$COMPOSE exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --no-owner --no-privileges --clean --if-exists > "$SAFETY_FILE" || true
chmod 600 "$SAFETY_FILE"
echo "    Wrote ${SAFETY_FILE}"

# --- 3. Import -------------------------------------------------------------
echo
echo ">>> [3/4] Importing into the Droplet database..."
$COMPOSE stop web
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -v ON_ERROR_STOP=1 --quiet < "$DUMP_FILE"
$COMPOSE start web

# --- 4. Verify -------------------------------------------------------------
echo
echo ">>> [4/4] Verifying..."
sleep 10
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
    "SELECT 'auth_user' AS relation, count(*) FROM auth_user
     UNION ALL
     SELECT 'django_session', count(*) FROM django_session;"

echo
echo ">>> Confirming migrations are in sync..."
$COMPOSE exec -T web python manage.py migrate --check --noinput \
    && echo "    Schema matches the code." \
    || echo "    WARNING: pending migrations. Run: $COMPOSE exec web python manage.py migrate"

echo
echo "=============================================================="
echo " Import complete: $(date -u +%FT%TZ)"
echo
echo " Next, in order:"
echo "   1. Log in on the test URL and confirm accounts came across."
echo "   2. Change the DNS A record to this Droplet's IP."
echo "   3. Watch: $COMPOSE logs -f web"
echo
echo " To roll back the import (not the DNS):"
echo "   ./ops/restore-plain.sh ${SAFETY_FILE}"
echo "=============================================================="
