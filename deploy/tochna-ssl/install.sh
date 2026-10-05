#!/usr/bin/env bash
#
# Install (or update) the token-free tenant-SSL sync on the production host.
# Idempotent: safe to re-run after editing any of the files here.
#
#   sudo bash deploy/tochna-ssl/install.sh
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

if [ "$(id -u)" -ne 0 ]; then
    echo "run as root (sudo bash $0)" >&2
    exit 1
fi

install -m 0755 "$HERE/sync_tochna_ssl.sh"       /usr/local/bin/sync_tochna_ssl.sh
install -m 0644 "$HERE/tochna-ssl-sync.service"  /etc/systemd/system/tochna-ssl-sync.service
install -m 0644 "$HERE/tochna-ssl-sync.timer"    /etc/systemd/system/tochna-ssl-sync.timer

systemctl daemon-reload
systemctl enable --now tochna-ssl-sync.timer

echo "== initial sync =="
/usr/local/bin/sync_tochna_ssl.sh || true

echo "== timer =="
systemctl list-timers tochna-ssl-sync.timer --no-pager || true
