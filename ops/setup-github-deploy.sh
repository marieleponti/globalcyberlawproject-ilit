#!/usr/bin/env bash
#
# Set up GitHub Actions deployment access on the Droplet.
#
#   ./ops/setup-github-deploy.sh
#
# Run once on the Droplet, as the deploy user, after the application is running.
#
# What this does, and why it is safe enough to put a key into GitHub:
#
# It creates a dedicated SSH key whose authorized_keys entry is pinned to a
# single forced command. When GitHub connects with that key, the Droplet ignores
# whatever command was requested and runs ops/deploy.sh instead. The key cannot
# open a shell, read a file, copy anything out, or forward a port. If it ever
# leaks, the worst an attacker can do is redeploy the current contents of the
# main branch, which is already public.
#
# That is the difference between "a key to the server lives in GitHub" and "a
# button that says deploy lives in GitHub". Only the second one is acceptable
# for a site under a vendor security review.

set -euo pipefail

cd "$(dirname "$0")/.."
REPO_DIR="$(pwd)"

if [[ "$EUID" -eq 0 ]]; then
    echo "ERROR: run this as the deploy user, not root." >&2
    echo "  su - deploy && cd ${REPO_DIR} && ./ops/setup-github-deploy.sh" >&2
    exit 1
fi

KEY_PATH="${HOME}/.ssh/github_actions_deploy"
AUTH_KEYS="${HOME}/.ssh/authorized_keys"
DEPLOY_SCRIPT="${REPO_DIR}/ops/deploy.sh"

if [[ ! -x "$DEPLOY_SCRIPT" ]]; then
    echo "ERROR: ${DEPLOY_SCRIPT} is missing or not executable." >&2
    exit 1
fi

mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"
touch "$AUTH_KEYS"
chmod 600 "$AUTH_KEYS"

# --- 1. Key ----------------------------------------------------------------
if [[ -f "$KEY_PATH" ]]; then
    echo ">>> A key already exists at ${KEY_PATH}."
    read -r -p "    Replace it? Existing GitHub secrets will stop working. [y/N] " reply
    if [[ "$reply" != "y" && "$reply" != "Y" ]]; then
        echo "    Keeping the existing key. Re-printing the values below."
    else
        rm -f "$KEY_PATH" "${KEY_PATH}.pub"
        # Drop the old entry so it cannot be used any more.
        grep -v "github-actions-deploy" "$AUTH_KEYS" > "${AUTH_KEYS}.tmp" || true
        mv "${AUTH_KEYS}.tmp" "$AUTH_KEYS"
        chmod 600 "$AUTH_KEYS"
    fi
fi

if [[ ! -f "$KEY_PATH" ]]; then
    echo ">>> Generating a dedicated deploy key..."
    ssh-keygen -t ed25519 -N "" -f "$KEY_PATH" -C "github-actions-deploy" >/dev/null
fi

# --- 2. Restricted authorized_keys entry -----------------------------------
# `restrict` disables port forwarding, agent forwarding, X11 and pty allocation.
# `command=` overrides whatever the client asks for.
PUBKEY="$(cat "${KEY_PATH}.pub")"
ENTRY="restrict,command=\"${DEPLOY_SCRIPT}\" ${PUBKEY}"

if ! grep -qF "github-actions-deploy" "$AUTH_KEYS"; then
    echo "$ENTRY" >> "$AUTH_KEYS"
    echo ">>> Added the restricted entry to authorized_keys."
else
    echo ">>> The restricted entry is already present."
fi
chmod 600 "$AUTH_KEYS"

# --- 3. Host key ------------------------------------------------------------
PUBLIC_IP="$(curl -fsS --max-time 10 https://api.ipify.org || echo "")"
if [[ -z "$PUBLIC_IP" ]]; then
    echo ">>> WARNING: could not determine the public IP. Fill DEPLOY_HOST in by hand."
    PUBLIC_IP="<droplet-ip>"
fi
KNOWN_HOSTS="$(ssh-keyscan -t ed25519 "$PUBLIC_IP" 2>/dev/null || echo "")"

# --- 4. Output --------------------------------------------------------------
cat <<EOF

==============================================================
 Add these as repository secrets on GitHub

   Settings > Secrets and variables > Actions > New secret

 Better still, create an Environment named "production" first
 (Settings > Environments) and add them there. That lets you
 require an approval before any deploy reaches the live site.
==============================================================

--- DEPLOY_HOST ---
${PUBLIC_IP}

--- DEPLOY_USER ---
$(whoami)

--- DEPLOY_KNOWN_HOSTS ---
${KNOWN_HOSTS}

--- SMOKE_URL ---
https://<your-domain>

--- DEPLOY_SSH_KEY (everything between the dashed lines, inclusive) ---
$(cat "$KEY_PATH")

==============================================================
 After pasting the private key into GitHub, wipe it from this
 terminal's history and scrollback:

   clear && history -c

 The private key stays on this Droplet at:
   ${KEY_PATH}
 You can delete it once GitHub has it. The public half in
 authorized_keys is what matters here.
==============================================================

 To verify the restriction works, try to get a shell with it:

   ssh -i ${KEY_PATH} $(whoami)@${PUBLIC_IP} "cat /etc/passwd"

 It should run a deployment instead of printing that file.
 If it prints the file, the forced command is not in place and
 you must not put this key into GitHub.

==============================================================
EOF
