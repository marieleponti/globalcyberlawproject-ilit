#!/usr/bin/env bash
#
# Issues a Let's Encrypt certificate for one additional domain sharing this
# Droplet's nginx, reusing the same certbot container docker-compose.prod.yml
# already runs. Companion to init-letsencrypt.sh, which is specific to
# $DOMAIN/$WWW_DOMAIN (this repo's own Django app). Use this one for any
# other domain added to nginx/templates/, e.g. the EB site's two subdomains.
#
#   ./ops/issue-cert.sh test.everywhereborder.org
#   STAGING=1 ./ops/issue-cert.sh test.everywhereborder.org   # rehearsal first
#
# Safe to run even before nginx has ever loaded a template referencing this
# domain's certificate paths: it writes a self-signed placeholder first
# (same sequence init-letsencrypt.sh uses for $DOMAIN), so a template
# pointing at /etc/letsencrypt/live/<domain>/... never crashes nginx —
# including the traffic for every other domain this same nginx serves.
#
# Prerequisites: DNS for the domain must already resolve to this Droplet,
# and a template with a server block for it must already be in
# nginx/templates/ (the placeholder step brings nginx up serving it).

set -euo pipefail
cd "$(dirname "$0")/.."

DOMAIN="${1:?Usage: ops/issue-cert.sh <domain>}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file ${ENV_FILE}"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found." >&2
    exit 1
fi

# shellcheck source=ops/load-env.sh
. "$(dirname "$0")/load-env.sh"
load_env "$ENV_FILE"

: "${CERTBOT_EMAIL:?CERTBOT_EMAIL must be set in $ENV_FILE}"

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

if $COMPOSE run --rm --entrypoint sh certbot -c "[ -f ${CERT_PATH}/fullchain.pem ]" 2>/dev/null; then
    echo ">>> A certificate for ${DOMAIN} already exists, skipping the placeholder."
else
    echo ">>> Creating a self-signed placeholder for ${DOMAIN} so nginx can start..."
    $COMPOSE run --rm --entrypoint sh certbot -c "
        mkdir -p ${CERT_PATH} &&
        openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
            -keyout ${CERT_PATH}/privkey.pem \
            -out ${CERT_PATH}/fullchain.pem \
            -subj '/CN=localhost' &&
        cp ${CERT_PATH}/fullchain.pem ${CERT_PATH}/chain.pem"

    echo ">>> Starting/reloading nginx so it can pick up the placeholder..."
    $COMPOSE up -d nginx
    sleep 5
    $COMPOSE exec nginx nginx -s reload

    echo ">>> Removing the placeholder..."
    $COMPOSE run --rm --entrypoint sh certbot -c "
        rm -rf /etc/letsencrypt/live/${DOMAIN} \
               /etc/letsencrypt/archive/${DOMAIN} \
               /etc/letsencrypt/renewal/${DOMAIN}.conf"
fi

STAGING_ARG=()
if [[ "${STAGING:-0}" == "1" ]]; then
    echo ">>> STAGING mode: certificate will NOT be browser-trusted."
    STAGING_ARG=(--staging)
fi

echo ">>> Requesting the real certificate for ${DOMAIN}..."
$COMPOSE run --rm --entrypoint certbot certbot \
    certonly --webroot -w /var/www/certbot \
    "${STAGING_ARG[@]}" \
    --email "${CERTBOT_EMAIL}" \
    -d "${DOMAIN}" \
    --rsa-key-size 4096 \
    --agree-tos \
    --no-eff-email \
    --non-interactive

echo ">>> Reloading nginx with the real certificate..."
$COMPOSE exec nginx nginx -s reload

echo
echo ">>> Done. Verify with:"
echo "      curl -I https://${DOMAIN}/"
