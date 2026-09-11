#!/usr/bin/env bash
#
# Vulnerability and static analysis scan.
#
#   ./ops/security-scan.sh
#
# Covers the "do you scan for vulnerabilities" item on the Temple vendor
# security questionnaire. Three passes:
#
#   1. pip-audit  - known CVEs in the pinned Python dependencies
#   2. bandit     - insecure patterns in this project's own source
#   3. Django     - the framework's own deployment checklist
#
# Reports land in ops/reports/. Run before each deployment and keep the output,
# since the questionnaire asks for evidence of a recurring process, not a
# one-time result.
#
# Exit code is non-zero if pip-audit or bandit found something, so this can gate
# a deploy. Set SOFT_FAIL=1 to report without failing.

set -uo pipefail

cd "$(dirname "$0")/.."

REPORT_DIR="ops/reports"
TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$REPORT_DIR"

FAILED=0

echo "=============================================================="
echo " Security scan - $(date -u +%FT%TZ)"
echo "=============================================================="

# --- 1. Dependency CVEs -----------------------------------------------------
echo
echo ">>> [1/3] pip-audit: known vulnerabilities in dependencies"
if ! command -v pip-audit >/dev/null 2>&1; then
    echo "    pip-audit not installed. Install with: pip install pip-audit"
    FAILED=1
else
    pip-audit -r src/requirements.txt \
        --format json \
        --output "${REPORT_DIR}/pip-audit-${TIMESTAMP}.json" || FAILED=1
    pip-audit -r src/requirements.txt || FAILED=1
    echo "    Report: ${REPORT_DIR}/pip-audit-${TIMESTAMP}.json"
fi

# --- 2. Static analysis -----------------------------------------------------
echo
echo ">>> [2/3] bandit: insecure patterns in src/"
if ! command -v bandit >/dev/null 2>&1; then
    echo "    bandit not installed. Install with: pip install bandit"
    FAILED=1
else
    # B101 (assert) is noise in Django projects; migrations and tests are
    # excluded because findings there are not reachable in production.
    bandit -r src/ \
        --exclude src/staticfiles,src/core/migrations,src/core/tests.py \
        --skip B101 \
        --format json \
        --output "${REPORT_DIR}/bandit-${TIMESTAMP}.json" || FAILED=1
    bandit -r src/ \
        --exclude src/staticfiles,src/core/migrations,src/core/tests.py \
        --skip B101 \
        --severity-level medium || FAILED=1
    echo "    Report: ${REPORT_DIR}/bandit-${TIMESTAMP}.json"
fi

# --- 3. Django deployment checklist ----------------------------------------
# Prefer running inside the container: the Droplet host has no Python
# dependencies installed, and the container is what actually ships.
echo
echo ">>> [3/3] Django deployment checklist"
if docker compose -f docker-compose.prod.yml --env-file .env.production \
        ps --status running web >/dev/null 2>&1 \
   && [[ -n "$(docker compose -f docker-compose.prod.yml --env-file .env.production \
        ps -q web 2>/dev/null)" ]]; then
    echo "    (running inside the web container)"
    docker compose -f docker-compose.prod.yml --env-file .env.production \
        exec -T web python manage.py check --deploy 2>&1 \
        | tee "${REPORT_DIR}/django-check-${TIMESTAMP}.txt" || FAILED=1
elif command -v python >/dev/null 2>&1; then
    if [[ -f .env.production ]]; then
        set -a
        # shellcheck disable=SC1091
        source .env.production
        set +a
    fi
    (cd src && DEBUG=False python manage.py check --deploy) 2>&1 \
        | tee "${REPORT_DIR}/django-check-${TIMESTAMP}.txt" || FAILED=1
else
    echo "    Skipped: no running web container and no local Python."
fi

echo
echo "=============================================================="
if [[ "$FAILED" -eq 0 ]]; then
    echo " Clean. Reports in ${REPORT_DIR}/"
    exit 0
fi
echo " Findings reported above. Reports in ${REPORT_DIR}/"
if [[ "${SOFT_FAIL:-0}" == "1" ]]; then
    exit 0
fi
exit 1
