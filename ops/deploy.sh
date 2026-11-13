#!/usr/bin/env bash
#
# Pull, rebuild, and restart the production stack on the Droplet.
#
#   ./ops/deploy.sh
#
# Takes a database backup first, so a migration that goes wrong has a way back.
# Nginx is never restarted, so TLS termination stays up and the outage is just
# the web container swap, normally a few seconds.
#
# Set SKIP_BACKUP=1 only for a change you are certain does not touch the schema.

set -euo pipefail

# GitHub Actions invokes this as a forced SSH command, which gets a minimal
# non-login shell. Set PATH explicitly so git and docker resolve there too.
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

# Resolve to an absolute path before changing directory: the re-exec below
# reuses $0, and a relative one stops resolving once we have moved.
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
cd "$(dirname "$SCRIPT_PATH")/.."

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file ${ENV_FILE}"
BRANCH="${BRANCH:-main}"

# Keep a local record of every deployment, including the ones triggered
# remotely, so a failed automated deploy can be diagnosed from the Droplet.
#
# Re-running through a pipe rather than using `exec > >(tee)`: process
# substitution can let the script exit before tee flushes, which truncates the
# last lines of a failed deploy over SSH. Here the parent waits for tee, and
# PIPESTATUS carries the real exit code back out.
LOG_DIR="${LOG_DIR:-./ops/reports}"
mkdir -p "$LOG_DIR"
if [[ -z "${_DEPLOY_LOGGING:-}" ]]; then
    export _DEPLOY_LOGGING=1
    set +e
    "$SCRIPT_PATH" "$@" 2>&1 | tee -a "${LOG_DIR}/deploy.log"
    exit "${PIPESTATUS[0]}"
fi

echo "=============================================================="
echo " Deploy - $(date -u +%FT%TZ)"
echo "=============================================================="

if [[ "${SKIP_BACKUP:-0}" != "1" ]]; then
    echo
    echo ">>> [1/5] Backing up the database..."
    ./ops/backup.sh
else
    echo
    echo ">>> [1/5] Backup skipped (SKIP_BACKUP=1)."
fi

echo
echo ">>> [2/5] Fetching ${BRANCH}..."
git fetch --quiet origin "$BRANCH"
PREVIOUS="$(git rev-parse HEAD)"
git checkout --quiet "$BRANCH"
git reset --hard --quiet "origin/${BRANCH}"
echo "    ${PREVIOUS:0:8} -> $(git rev-parse --short HEAD)"

echo
echo ">>> [3/5] Rebuilding the web image..."
$COMPOSE build web

echo
echo ">>> [4/5] Restarting the web container..."
# Migrations and collectstatic run in the entrypoint on start.
$COMPOSE up -d --no-deps web

echo
echo ">>> [5/5] Waiting for the health check..."
for i in $(seq 1 30); do
    STATUS="$(docker inspect --format='{{.State.Health.Status}}' gclp_web 2>/dev/null || echo starting)"
    if [[ "$STATUS" == "healthy" ]]; then
        echo "    Healthy after $((i * 2))s."
        echo
        echo "=============================================================="
        echo " Deployed $(git rev-parse --short HEAD)"
        echo "=============================================================="
        exit 0
    fi
    sleep 2
done

echo "    ERROR: the container did not become healthy within 60s." >&2
echo >&2
$COMPOSE logs --tail=50 web >&2
echo >&2
echo "    To roll back:" >&2
echo "      git reset --hard ${PREVIOUS} && ./ops/deploy.sh" >&2
exit 1
