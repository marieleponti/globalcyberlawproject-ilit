#!/usr/bin/env bash
#
# One-time hardening of a fresh Ubuntu Droplet, run as root before the first
# deployment.
#
#   ssh root@<droplet-ip>
#   bash harden-droplet.sh
#
# Covers the host-level items on the Temple vendor security questionnaire:
# firewall, no password SSH, automatic security updates, brute-force protection,
# and encryption at rest for the Postgres volume.
#
# Read it before running it. It changes SSH configuration, and a mistake there
# can lock you out of the Droplet. Keep the DigitalOcean web console open in
# another tab as a way back in.

set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
    echo "Run as root." >&2
    exit 1
fi

DEPLOY_USER="${DEPLOY_USER:-deploy}"
SSH_PORT="${SSH_PORT:-22}"

echo "=============================================================="
echo " Droplet hardening"
echo "=============================================================="

# --- 1. Updates -------------------------------------------------------------
echo
echo ">>> [1/7] Updating packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    ufw fail2ban unattended-upgrades apt-listchanges \
    ca-certificates curl gnupg cryptsetup

# --- 2. Unattended security updates ----------------------------------------
echo
echo ">>> [2/7] Enabling automatic security updates..."
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
cat > /etc/apt/apt.conf.d/50unattended-upgrades <<'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
systemctl enable --now unattended-upgrades

# --- 3. Deploy user ---------------------------------------------------------
echo
echo ">>> [3/7] Creating the ${DEPLOY_USER} user..."
if ! id -u "$DEPLOY_USER" >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" "$DEPLOY_USER"
fi
usermod -aG sudo "$DEPLOY_USER"

# Copy root's authorized keys so the same SSH key works for the new user.
if [[ -f /root/.ssh/authorized_keys ]]; then
    mkdir -p "/home/${DEPLOY_USER}/.ssh"
    cp /root/.ssh/authorized_keys "/home/${DEPLOY_USER}/.ssh/authorized_keys"
    chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "/home/${DEPLOY_USER}/.ssh"
    chmod 700 "/home/${DEPLOY_USER}/.ssh"
    chmod 600 "/home/${DEPLOY_USER}/.ssh/authorized_keys"
    echo "    Copied root's SSH keys to ${DEPLOY_USER}."
else
    echo "    WARNING: /root/.ssh/authorized_keys is missing."
    echo "    Add a key for ${DEPLOY_USER} BEFORE the SSH step below, or you"
    echo "    will be locked out."
fi

# --- 4. SSH -----------------------------------------------------------------
echo
echo ">>> [4/7] Hardening SSH..."
echo "    Confirm you can open a SECOND session as ${DEPLOY_USER} right now."
read -r -p "    Is key-based login as ${DEPLOY_USER} confirmed working? [y/N] " reply
if [[ "$reply" == "y" || "$reply" == "Y" ]]; then
    cat > /etc/ssh/sshd_config.d/99-hardening.conf <<EOF
Port ${SSH_PORT}
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
X11Forwarding no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers ${DEPLOY_USER}
EOF
    sshd -t && systemctl restart ssh
    echo "    SSH hardened: root login and passwords disabled."
else
    echo "    Skipped. Re-run this script once key login is working."
fi

# --- 5. Firewall ------------------------------------------------------------
echo
echo ">>> [5/7] Configuring the firewall..."
ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw allow "${SSH_PORT}/tcp" comment 'SSH'
ufw allow 80/tcp  comment 'HTTP (ACME + redirect)'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
ufw status verbose

# Docker publishes ports by writing iptables rules that bypass ufw. Only nginx
# publishes anything, and only on 80/443, so this is consistent either way. The
# database publishes nothing at all.

# --- 6. fail2ban ------------------------------------------------------------
echo
echo ">>> [6/7] Configuring fail2ban..."
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
backend  = systemd

[sshd]
enabled = true
port    = ${SSH_PORT}
EOF
systemctl enable --now fail2ban
systemctl restart fail2ban

# --- 7. Docker --------------------------------------------------------------
echo
echo ">>> [7/7] Installing Docker Engine..."
if ! command -v docker >/dev/null 2>&1; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
fi
usermod -aG docker "$DEPLOY_USER"
systemctl enable --now docker

# Cap container log growth globally, as a second line of defence alongside the
# per-service limits in docker-compose.prod.yml.
cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" },
  "live-restore": true
}
EOF
systemctl restart docker

echo
echo "=============================================================="
echo " Host hardening complete."
echo
echo " Still to do by hand:"
echo
echo "   1. Encryption at rest for the database. DigitalOcean encrypts Droplet"
echo "      disks at the platform level, which the questionnaire may accept as"
echo "      written. For encryption you control, attach a Block Storage volume"
echo "      and run ops/setup-encrypted-volume.sh."
echo
echo "   2. Enable DigitalOcean weekly Droplet backups in the control panel."
echo "      These are separate from ops/backup.sh and protect against losing"
echo "      the whole Droplet rather than just the data."
echo
echo "   3. Reboot to load the new kernel: reboot"
echo "=============================================================="
