#!/usr/bin/env bash
#
# First-time TLS certificate issuance on the Droplet.
#
#   ./ops/init-letsencrypt.sh
#
# Run once, after DNS for $DOMAIN already points at this Droplet. Let's Encrypt
# validates over HTTP-01, which means it resolves the domain and fetches a file
# from port 80 here. If DNS still points at Render, issuance fails.
#
# For a dry run against a test subdomain, set STAGING=1 to use Let's Encrypt's
# staging CA. Staging certificates are not trusted by browsers but are not rate
# limited, so use them while working out the configuration.
#
# Sequence: a self-signed placeholder is written first so nginx can start at
# all, then it is replaced by the real certificate and nginx reloads.

set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file ${ENV_FILE}"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found. Copy .env.production.example and fill it in." >&2
    exit 1
fi

# shellcheck source=ops/load-env.sh
. "$(dirname "$0")/load-env.sh"
load_env "$ENV_FILE"

: "${DOMAIN:?DOMAIN must be set in $ENV_FILE}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL must be set in $ENV_FILE}"

DOMAIN_ARGS=(-d "$DOMAIN")
if [[ -n "${WWW_DOMAIN:-}" ]]; then
    DOMAIN_ARGS+=(-d "$WWW_DOMAIN")
fi

STAGING_ARG=()
if [[ "${STAGING:-0}" == "1" ]]; then
    echo ">>> STAGING mode: certificates will NOT be browser-trusted."
    STAGING_ARG=(--staging)
fi

CERT_PATH="/etc/letsencrypt/live/${DOMAIN}"

echo ">>> Checking DNS for ${DOMAIN}..."
RESOLVED="$(getent hosts "$DOMAIN" | awk '{print $1}' | head -1 || true)"
PUBLIC_IP="$(curl -fsS --max-time 10 https://api.ipify.org || true)"
if [[ -n "$RESOLVED" && -n "$PUBLIC_IP" && "$RESOLVED" != "$PUBLIC_IP" ]]; then
    echo "    WARNING: ${DOMAIN} resolves to ${RESOLVED}, this host is ${PUBLIC_IP}."
    echo "    HTTP-01 validation will fail until DNS points here."
    read -r -p "    Continue anyway? [y/N] " reply
    [[ "$reply" == "y" || "$reply" == "Y" ]] || exit 1
fi

echo ">>> Creating a self-signed placeholder so nginx can start..."
$COMPOSE run --rm --entrypoint sh certbot -c "
    mkdir -p ${CERT_PATH} &&
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout ${CERT_PATH}/privkey.pem \
        -out ${CERT_PATH}/fullchain.pem \
        -subj '/CN=localhost' &&
    cp ${CERT_PATH}/fullchain.pem ${CERT_PATH}/chain.pem"

echo ">>> Starting nginx..."
$COMPOSE up -d nginx
sleep 5

echo ">>> Removing the placeholder..."
$COMPOSE run --rm --entrypoint sh certbot -c "
    rm -rf /etc/letsencrypt/live/${DOMAIN} \
           /etc/letsencrypt/archive/${DOMAIN} \
           /etc/letsencrypt/renewal/${DOMAIN}.conf"

echo ">>> Requesting the real certificate..."
$COMPOSE run --rm --entrypoint certbot certbot \
    certonly --webroot -w /var/www/certbot \
    "${STAGING_ARG[@]}" \
    --email "${CERTBOT_EMAIL}" \
    "${DOMAIN_ARGS[@]}" \
    --rsa-key-size 4096 \
    --agree-tos \
    --no-eff-email \
    --non-interactive

echo ">>> Reloading nginx with the real certificate..."
$COMPOSE exec nginx nginx -s reload

echo
echo ">>> Done. Verify with:"
echo "      curl -I https://${DOMAIN}/healthz"
echo "      https://www.ssllabs.com/ssltest/analyze.html?d=${DOMAIN}"
echo
echo ">>> Renewal is automatic: the certbot container retries every 12 hours"
echo "    and nginx reloads on the same cadence."
