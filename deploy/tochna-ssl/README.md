# Tenant SSL — token-free auto-provisioning

Every organization has its own entrance at `<slug>.tochna.uz`. Each such host
needs a valid TLS certificate at the origin. This folder provisions and renews
those certificates automatically, for existing **and future** organizations,
without any Cloudflare DNS-01 token.

## How it works

- A **DNS-only wildcard** record `*.tochna.uz → <origin IP>` already exists, so
  any new subdomain resolves to this server the moment an org is created.
- `sync_tochna_ssl.sh` asks Django for the current org hosts
  (`manage.py print_tenant_hosts`), and when that set changes it:
  1. reissues one shared cert `tochna-tenants` via **HTTP-01** (`certbot
     --nginx`; the `*.tochna.uz` server block answers the ACME challenge),
  2. rewrites the tenant vhost `server_name` to the current host set,
  3. `nginx -t` and a graceful `systemctl reload nginx`.
- `tochna-ssl-sync.timer` runs it ~every 30 min, so a new org is covered within
  one interval. When nothing changed the run is a no-op (no certbot call, no
  reload).
- Ordinary renewals are handled by the system `certbot.timer`; the deploy hook
  `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh` reloads nginx after a
  renewal. This sync job only reacts to the host set changing.

## Install / update

```bash
sudo bash deploy/tochna-ssl/install.sh
```

## Operate

```bash
sudo /usr/local/bin/sync_tochna_ssl.sh      # run now (no-op if unchanged)
systemctl list-timers tochna-ssl-sync.timer # next run
journalctl -u tochna-ssl-sync.service -n 50 # last run log
sudo certbot certificates                   # what the cert currently covers
```

State lives in `/var/lib/tochna-ssl/hosts` (the last successfully certified
set). A timestamped backup of the vhost is written next to it on each change.

## Limits

- Let's Encrypt allows up to 100 names per certificate. Past ~100 organizations,
  switch to a wildcard cert (DNS-01, needs a `Zone:DNS:Edit` token) — see
  `setup_wildcard_ssl.sh` in the session scratchpad for that path.
- Deleting an org drops its host from `server_name` on the next run (its
  subdomain then falls back to the self-signed wildcard block); the name is not
  actively removed from the cert until the next reissue for another reason.
