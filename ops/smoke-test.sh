#!/usr/bin/env bash
#
# Hit every public route and report the status code.
#
#   ./ops/smoke-test.sh https://test.nationalstatements.org
#   ./ops/smoke-test.sh http://localhost:8000
#
# Run this against the test URL before the cutover, and against the real domain
# immediately after the DNS change. It is the fastest way to tell whether a
# visualization broke in the move, since a Plotly failure surfaces as a 500 on
# one route while everything else stays green.
#
# If the site is still login-gated, pass credentials so the session cookie is
# carried through:
#   USERNAME=admin PASSWORD=secret ./ops/smoke-test.sh https://test.example.org

set -uo pipefail

BASE_URL="${1:-http://localhost:8000}"
BASE_URL="${BASE_URL%/}"
COOKIE_JAR="$(mktemp)"
trap 'rm -f "$COOKIE_JAR"' EXIT

PASS=0
FAIL=0
FAILED_ROUTES=()

# Every route in src/core/urls.py, plus the health endpoints.
ROUTES=(
    "/healthz"
    "/readyz"
    "/"
    "/methodology"
    "/about"
    "/source-docs"
    "/contact"
    "/uof"
    "/sovereignty"
    "/nonintervention"
    "/selfdefense"
    "/uof-sankey"
    "/uof-demscore-sankey"
    "/uof-scatter"
    "/uof-by-state-scatter"
    "/uof-sovereignty-parallel-categories"
    "/uof-eu-states-to-eu-uof"
    "/uof-art51-nato-sankey"
    "/uof-q8-sunburst"
    "/sovereignty-sankey"
    "/sov-demscore-sankey"
    "/sov-eu-states-to-eu"
    "/sov-non-eu-states-to-eu"
    "/sov-by-state-scatter"
    "/nonintervention-sankey"
    "/nonint-demscore-sankey"
    "/nonint-eu-states-to-eu"
    "/nonint-non-eu-states-to-eu"
    "/nonint-by-state-scatter"
    "/selfdefense-sankey"
    "/selfdefense-demscore-sankey"
    "/selfdefense-eu-states-to-eu"
    "/selfdefense-non-eu-states-to-eu"
    "/selfdefense-by-state-scatter"
    "/statements-choropleth/"
)

echo "=============================================================="
echo " Smoke test: ${BASE_URL}"
echo " Started: $(date -u +%FT%TZ)"
echo "=============================================================="

# --- Optional login ---------------------------------------------------------
if [[ -n "${USERNAME:-}" && -n "${PASSWORD:-}" ]]; then
    echo
    echo ">>> Logging in as ${USERNAME}..."
    CSRF="$(curl -fsS -c "$COOKIE_JAR" "${BASE_URL}/login/" \
        | grep -o 'name="csrfmiddlewaretoken" value="[^"]*"' \
        | head -1 | cut -d'"' -f4)"
    if [[ -z "$CSRF" ]]; then
        echo "    Could not read a CSRF token from the login page." >&2
    else
        curl -fsS -o /dev/null -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
            -e "${BASE_URL}/login/" \
            -d "csrfmiddlewaretoken=${CSRF}" \
            -d "username=${USERNAME}" \
            -d "password=${PASSWORD}" \
            "${BASE_URL}/login/" && echo "    Logged in." \
            || echo "    Login failed; routes will be tested anonymously." >&2
    fi
fi

# --- Routes -----------------------------------------------------------------
echo
for route in "${ROUTES[@]}"; do
    START="$(date +%s%N)"
    CODE="$(curl -sS -o /dev/null -w '%{http_code}' \
        --max-time 60 \
        -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
        "${BASE_URL}${route}" 2>/dev/null || echo "000")"
    MS=$(( ($(date +%s%N) - START) / 1000000 ))

    case "$CODE" in
        200|301|302)
            printf '  %-6s %-45s %sms\n' "OK" "$route" "$MS"
            PASS=$((PASS + 1))
            ;;
        *)
            printf '  %-6s %-45s %sms  <-- HTTP %s\n' "FAIL" "$route" "$MS" "$CODE"
            FAIL=$((FAIL + 1))
            FAILED_ROUTES+=("${route} (HTTP ${CODE})")
            ;;
    esac
done

# --- TLS --------------------------------------------------------------------
if [[ "$BASE_URL" == https://* ]]; then
    echo
    echo ">>> Certificate:"
    HOSTNAME_ONLY="${BASE_URL#https://}"
    HOSTNAME_ONLY="${HOSTNAME_ONLY%%/*}"
    echo | openssl s_client -connect "${HOSTNAME_ONLY}:443" \
        -servername "$HOSTNAME_ONLY" 2>/dev/null \
        | openssl x509 -noout -subject -issuer -dates 2>/dev/null \
        | sed 's/^/    /' || echo "    Could not read the certificate."
fi

echo
echo "=============================================================="
echo " Passed: ${PASS}    Failed: ${FAIL}"
if [[ "$FAIL" -gt 0 ]]; then
    echo
    echo " Failing routes:"
    printf '   - %s\n' "${FAILED_ROUTES[@]}"
    echo "=============================================================="
    exit 1
fi
echo "=============================================================="
