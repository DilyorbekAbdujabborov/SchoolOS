#!/usr/bin/env bash
#
# Keep a valid Let's Encrypt certificate for every organization subdomain
# (<slug>.<TENANT_BASE_DOMAIN>) with no DNS-01 token required.
#
# How it works, every run:
#   1. Ask Django for the current set of org tenant hosts.
#   2. If that set is unchanged since last run -> do nothing (no certbot call,
#      no nginx reload). Renewals of the existing cert are handled separately by
#      certbot.timer, so this job only reacts to organizations being added.
#   3. If it changed -> reissue the shared "tochna-tenants" cert with HTTP-01
#      (nginx authenticator; the wildcard "*.<base>" server block answers the
#      ACME challenge), point the tenant vhost's server_name at the new set, and
#      reload nginx.
#
# Prerequisite already satisfied on this zone: a DNS-only wildcard
# "*.<TENANT_BASE_DOMAIN>" A record points at this origin, so any new subdomain
# resolves here immediately and HTTP-01 can validate it.
#
# Installed at /usr/local/bin/sync_tochna_ssl.sh and run by tochna-ssl-sync.timer
# as root. Safe to run by hand at any time.

set -euo pipefail

APP_DIR=/var/www/SchoolOS/backend
PYTHON="$APP_DIR/venv/bin/python"
export DJANGO_SETTINGS_MODULE=config.settings.production

CERT_NAME=tochna-tenants
VHOST=/etc/nginx/sites-available/tochna-tenants
EMAIL=admin@tochna.uz

STATE_DIR=/var/lib/tochna-ssl
STATE="$STATE_DIR/hosts"
LOCK="$STATE_DIR/.lock"

log() { printf '%s %s\n' "$(date '+%F %T')" "$*"; }

mkdir -p "$STATE_DIR"

# Serialize: a long certbot run must not overlap the next timer tick.
exec 9>"$LOCK"
flock -n 9 || { log "another run in progress; skip"; exit 0; }

# 1. Current org tenant hosts, sorted and de-duplicated.
mapfile -t HOSTS < <(cd "$APP_DIR" && "$PYTHON" manage.py print_tenant_hosts)
if [ "${#HOSTS[@]}" -eq 0 ]; then
    log "no tenant hosts returned; aborting to avoid wiping the cert"
    exit 0
fi
NEW=$(printf '%s\n' "${HOSTS[@]}" | sort -u)

# 2. No change since last successful run -> nothing to do.
OLD=$(cat "$STATE" 2>/dev/null || true)
if [ "$NEW" = "$OLD" ]; then
    log "host set unchanged ($(printf '%s\n' "$NEW" | wc -l) hosts); nothing to do"
    exit 0
fi

log "host set changed; reissuing '$CERT_NAME' for:"
printf '  %s\n' $NEW

# 3. (Re)issue the shared cert with exactly the current host set.
DARGS=()
while IFS= read -r h; do DARGS+=(-d "$h"); done <<< "$NEW"
certbot certonly --nginx --cert-name "$CERT_NAME" --expand \
    "${DARGS[@]}" \
    --non-interactive --agree-tos -m "$EMAIL" \
    --keep-until-expiring

# 4. Point the tenant vhost server_name at the current host set.
NAMES=$(printf '%s ' $NEW | sed 's/ $//')
cp -a "$VHOST" "$VHOST.bak.$(date +%s)"
sed -i -E "s/^([[:space:]]*server_name[[:space:]]+).*;/\1$NAMES;/" "$VHOST"

# 5. Validate and reload (graceful; no dropped connections).
nginx -t
systemctl reload nginx

# 6. Record the host set only after everything succeeded.
printf '%s\n' "$NEW" > "$STATE"
log "done: $(printf '%s\n' "$NEW" | wc -l) tenant hosts certified"
