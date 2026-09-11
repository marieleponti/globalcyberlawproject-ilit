#!/usr/bin/env bash
#
# Encrypt the Postgres data directory at rest with LUKS on a DigitalOcean Block
# Storage volume.
#
#   DEVICE=/dev/disk/by-id/scsi-0DO_Volume_gclp-data ./ops/setup-encrypted-volume.sh
#
# Run as root, once, on a fresh volume, BEFORE the first `docker compose up`.
# It destroys everything on the target device.
#
# Why this exists: the Temple vendor questionnaire asks about encryption at rest.
# DigitalOcean encrypts the underlying storage at the platform level, which may
# satisfy the question as written. This gives you a key you control instead,
# which is a stronger answer.
#
# The trade-off is real and you should accept it deliberately: a LUKS volume
# must be unlocked with the passphrase after every reboot, before Docker starts,
# or Postgres comes up against an empty directory. That means the Droplet cannot
# boot back into service unattended. Decide which matters more for this project.

set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
    echo "Run as root." >&2
    exit 1
fi

DEVICE="${DEVICE:?Set DEVICE to the block device, e.g. /dev/sda}"
MAPPER_NAME="${MAPPER_NAME:-gclp_crypt}"
MOUNT_POINT="${MOUNT_POINT:-/mnt/gclp-data}"

if [[ ! -b "$DEVICE" ]]; then
    echo "ERROR: $DEVICE is not a block device." >&2
    lsblk
    exit 1
fi

echo "=============================================================="
echo " LUKS setup on ${DEVICE}"
echo "=============================================================="
lsblk "$DEVICE"
echo
echo " This ERASES everything on ${DEVICE}."
read -r -p " Type ERASE to continue: " reply
[[ "$reply" == "ERASE" ]] || { echo "Aborted."; exit 1; }

echo
echo ">>> [1/5] Creating the LUKS container..."
echo "    Choose a strong passphrase and store it in your password manager."
echo "    If it is lost, the data is unrecoverable. There is no backdoor."
cryptsetup luksFormat --type luks2 \
    --cipher aes-xts-plain64 \
    --key-size 512 \
    --hash sha512 \
    --pbkdf argon2id \
    "$DEVICE"

echo
echo ">>> [2/5] Opening it..."
cryptsetup open "$DEVICE" "$MAPPER_NAME"

echo
echo ">>> [3/5] Creating the filesystem..."
mkfs.ext4 -q -L gclp-data "/dev/mapper/${MAPPER_NAME}"

echo
echo ">>> [4/5] Mounting at ${MOUNT_POINT}..."
mkdir -p "$MOUNT_POINT"
mount "/dev/mapper/${MAPPER_NAME}" "$MOUNT_POINT"
mkdir -p "${MOUNT_POINT}/postgres"
chmod 700 "${MOUNT_POINT}/postgres"

echo
echo ">>> [5/5] Recording fstab and crypttab entries..."
UUID="$(blkid -s UUID -o value "$DEVICE")"

# noauto: boot must not block waiting for a passphrase on a headless Droplet.
if ! grep -q "$MAPPER_NAME" /etc/crypttab 2>/dev/null; then
    echo "${MAPPER_NAME} UUID=${UUID} none luks,noauto" >> /etc/crypttab
fi
if ! grep -q "$MOUNT_POINT" /etc/fstab 2>/dev/null; then
    echo "/dev/mapper/${MAPPER_NAME} ${MOUNT_POINT} ext4 defaults,noauto 0 2" >> /etc/fstab
fi

cat <<EOF

==============================================================
 Encrypted volume ready at ${MOUNT_POINT}

 1. Point Postgres at it. In docker-compose.prod.yml, replace
    the named volume with a bind mount:

      volumes:
        postgres_data:
          driver: local
          driver_opts:
            type: none
            o: bind
            device: ${MOUNT_POINT}/postgres

 2. AFTER EVERY REBOOT, unlock before starting Docker:

      cryptsetup open ${DEVICE} ${MAPPER_NAME}
      mount ${MOUNT_POINT}
      cd /opt/globalcyberlawproject-ilit
      docker compose -f docker-compose.prod.yml --env-file .env.production up -d

    Docker is set to restart containers automatically, so consider
    masking that until the volume is mounted, or Postgres will
    initialise an empty database on the unmounted mount point.

 3. Store the passphrase off this Droplet.
==============================================================
EOF
