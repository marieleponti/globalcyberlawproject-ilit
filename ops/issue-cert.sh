#!/usr/bin/env bash
#
# Issues a Let's Encrypt certificate for one additional domain sharing this
# Droplet's nginx, reusing the certbot container docker-compose.prod.yml already
# runs. Companion to init-letsencrypt.sh, which is specific to $DOMAIN and
# $WWW_DOMAIN (this repo's own Django app). Use this one for any other domain
# added to nginx/templates/, e.g. the EB site's two subdomains.
#
# Order matters on a SHARED nginx, because a template that points at a missing
# certificate file stops nginx from starting at all, for every site on it:
#
#   1. PLACEHOLDER_ONLY=1 ./ops/issue-cert.sh <domain>     (once per domain)
#   2. enable the template and recreate nginx (see nginx/eb-site.conf.template.example)
#   3. STAGING=1 ./ops/issue-cert.sh <domain>               (rehearsal, not browser-trusted)
#   4. FORCE=1 ./ops/issue-cert.sh <domain>                 (the real one; FORCE because step 3
#                                                            left a staging certificate behind)
#
# Step 3 and 4 swap a placeholder for the real certificate. If the request
# fails, the placeholder is put back, so nginx is never left without the file
# its config names. A domain that already has a real certificate is skipped
# unless FORCE=1.
#
# Prerequisites for 3 and 4: DNS for the domain already resolves to this
# Droplet (with Cloudflare, DNS-only / grey cloud while issuing), and nginx is
# already serving a port-80 block for it so HTTP-01 has something to answer.

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
CERTBOT_SH() { $COMPOSE run --rm --entrypoint sh certbot -c "$1"; }

make_placeholder() {
    CERTBOT_SH "
        mkdir -p ${CERT_PATH} &&
        openssl req -x509 -nodes -newkey rsa:2048 -days 30 \
            -keyout ${CERT_PATH}/privkey.pem \
            -out ${CERT_PATH}/fullchain.pem \
            -subj '/CN=localhost' &&
        cp ${CERT_PATH}/fullchain.pem ${CERT_PATH}/chain.pem"
}

reload_nginx() {
    if $COMPOSE ps --status running --services 2>/dev/null | grep -qx nginx; then
        $COMPOSE exec -T nginx nginx -s reload
    fi
}

# A real, certbot-managed certificate leaves a renewal config behind.
HAS_REAL=0
CERTBOT_SH "[ -f /etc/letsencrypt/renewal/${DOMAIN}.conf ]" 2>/dev/null && HAS_REAL=1

if [[ "${PLACEHOLDER_ONLY:-0}" == "1" ]]; then
    if CERTBOT_SH "[ -f ${CERT_PATH}/fullchain.pem ]" 2>/dev/null; then
        echo ">>> A certificate (placeholder or real) already exists for ${DOMAIN}, nothing to do."
    else
        echo ">>> Writing a self-signed placeholder for ${DOMAIN}..."
        make_placeholder
    fi
    exit 0
fi

if [[ "$HAS_REAL" == "1" && "${FORCE:-0}" != "1" ]]; then
    echo ">>> ${DOMAIN} already has a real certificate. Set FORCE=1 to request it again."
    exit 0
fi

echo ">>> Checking DNS for ${DOMAIN}..."
RESOLVED="$(getent hosts "$DOMAIN" | awk '{print $1}' | head -1 || true)"
PUBLIC_IP="$(curl -fsS --max-time 10 https://api.ipify.org || true)"
if [[ -n "$RESOLVED" && -n "$PUBLIC_IP" && "$RESOLVED" != "$PUBLIC_IP" ]]; then
    echo "    WARNING: ${DOMAIN} resolves to ${RESOLVED}, this host is ${PUBLIC_IP}."
    echo "    HTTP-01 validation will fail until DNS points here (grey cloud on Cloudflare)."
    read -r -p "    Continue anyway? [y/N] " reply
    [[ "$reply" == "y" || "$reply" == "Y" ]] || exit 1
fi

# nginx must already be running with the placeholder in place; make sure one
# exists before touching anything.
CERTBOT_SH "[ -f ${CERT_PATH}/fullchain.pem ]" 2>/dev/null || { echo ">>> No certificate files yet, writing a placeholder first..."; make_placeholder; reload_nginx; sleep 3; }

STAGING_ARG=()
if [[ "${STAGING:-0}" == "1" ]]; then
    echo ">>> STAGING mode: certificate will NOT be browser-trusted."
    STAGING_ARG=(--staging)
fi

# certbot refuses to write into a live/<domain> directory it does not manage,
# so the placeholder has to go first. It is restored if the request fails.
echo ">>> Replacing the placeholder with a real certificate for ${DOMAIN}..."
CERTBOT_SH "rm -rf ${CERT_PATH} /etc/letsencrypt/archive/${DOMAIN} /etc/letsencrypt/renewal/${DOMAIN}.conf"

if ! $COMPOSE run --rm --entrypoint certbot certbot \
        certonly --webroot -w /var/www/certbot \
        "${STAGING_ARG[@]}" \
        --email "${CERTBOT_EMAIL}" \
        -d "${DOMAIN}" \
        --rsa-key-size 4096 \
        --agree-tos \
        --no-eff-email \
        --non-interactive; then
    echo ">>> ERROR: issuance failed. Restoring the placeholder so nginx keeps starting." >&2
    make_placeholder
    exit 1
fi

echo ">>> Reloading nginx with the new certificate..."
reload_nginx

echo
echo ">>> Done. Verify with:"
echo "      curl -I https://${DOMAIN}/"
if [[ "${STAGING:-0}" == "1" ]]; then
    echo ">>> That was a STAGING certificate. Run again with FORCE=1 and without STAGING for the real one."
fi
