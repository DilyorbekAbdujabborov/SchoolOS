#!/bin/sh
# Only the web (gunicorn) service needs to migrate + collect static on start —
# celery/beat/the Telegram bot share this same image but must not race each
# other running migrations concurrently.
set -e

if [ "$1" = "gunicorn" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
fi

exec "$@"
