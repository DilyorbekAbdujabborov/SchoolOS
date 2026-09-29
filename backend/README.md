# SchoolOS Backend

Django REST Framework backend for SchoolOS — a school CRM + learning platform
(attendance, classes, lessons, notifications, Telegram bot integration).

## 1. Purpose

This template provides a sane project structure with:

- Custom `User` model (email-based, unique email)
- Django REST Framework with pagination, filtering, search and ordering
- Auto-generated API documentation (Swagger / ReDoc / OpenAPI schema)
- Celery + Redis for background tasks
- Redis cache for production
- PostgreSQL support (SQLite out-of-the-box for local development)
- CORS support
- Separation of settings per environment
- Reusable `apps/common` utilities

## 2. Requirements

- Python 3.12+
- (optional, for Celery/cache) Redis running locally
- (optional, for production) PostgreSQL

## 3. Installation

Clone this template and rename it for your new project:

```bash
git clone <template-url> my-new-project
cd my-new-project
rm -rf .git  # start a fresh history
```

## 4. Virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate          # Windows
pip install --upgrade pip
pip install -r requirements/development.txt
```

## 5. Environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at least `DJANGO_SECRET_KEY` to a fresh random value:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

All variables are documented in `.env.example`. Never commit real `.env` files.

## 6. Database setup

### SQLite (default, local development)

Nothing to do. The template uses SQLite automatically.

### PostgreSQL (production)

Set in `.env`:

```env
DJANGO_DB_ENGINE=django.db.backends.postgresql
DJANGO_DB_NAME=my_db
DJANGO_DB_USER=my_user
DJANGO_DB_PASSWORD=my_password
DJANGO_DB_HOST=localhost
DJANGO_DB_PORT=5432
```

Install the production requirements, which include the PostgreSQL driver:

```bash
pip install -r requirements/production.txt
```

## 7. Running migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 8. Creating a superuser

```bash
python manage.py createsuperuser
```

The admin is available at `/admin/`.

## 9. Running the development server

```bash
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`.

## 10. Running Celery

Requires Redis running locally (`redis-server`).

Terminal 1 — Celery worker:

```bash
celery -A config worker -l info
```

Terminal 2 — Celery beat (only if you use scheduled tasks):

```bash
celery -A config beat -l info
```

## 11. Telegram bot

The bot has two delivery modes, sharing one set of handlers (`apps/telegram_bot/bot.py`):

| Mode | Command | Use when |
| --- | --- | --- |
| Long polling | `python manage.py runbot` | Local development — no public HTTPS URL needed |
| Webhook | `python manage.py telegram_webhook set` | Production — Telegram POSTs each update to `/api/telegram/webhook/` |

Telegram only allows one of the two at a time: with a webhook registered, `getUpdates`
fails with 409. Run `manage.py telegram_webhook delete` before switching back to polling.

### Setting up the webhook (production)

1. Add both variables to `.env` — the endpoint must be a public HTTPS URL served by your
   app, and the secret is checked against the `X-Telegram-Bot-Api-Secret-Token` header
   Telegram sends with every update:

   ```bash
   TELEGRAM_WEBHOOK_URL=https://your-domain.example/api/telegram/webhook/
   TELEGRAM_WEBHOOK_SECRET=  # python -c 'import secrets; print(secrets.token_hex(32))'
   ```

2. Register it and confirm:

   ```bash
   python manage.py telegram_webhook set
   python manage.py telegram_webhook info
   ```

No Celery worker or extra process is needed — the endpoint starts the bot on the
gunicorn worker's first update, and `getWebhookInfo` (`... telegram_webhook info`)
reports any delivery errors Telegram saw.

Users link their account by requesting a code in the web app, then sending
`/start <code>` to the bot.

## 12. API documentation

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

## 13. Creating a new app

```bash
python manage.py startapp myapp --settings=config.settings.development
mkdir -p apps/myapp
mv myapp/* apps/myapp/ && rmdir myapp
```

Then:

1. Add `"apps.myapp"` to `INSTALLED_APPS` in `config/settings/base.py`.
2. Create `apps/myapp/apps.py` with `name = "apps.myapp"` (see `apps/users/apps.py`).
3. Register API routes in `config/api_urls.py`:

```python
path("", include("apps.myapp.urls")),
```

Each app may contain: `models.py`, `serializers.py`, `views.py`, `urls.py`,
`admin.py`, `permissions.py`, `filters.py`, `services.py`, `tasks.py`.
Create only what you actually use.

Preferred pattern: REST Framework `ViewSet`s + a `DefaultRouter` in `urls.py`
for CRUD resources, plain APIViews for simple endpoints.

## 14. Recommended workflow for a new project

```bash
git clone <template-url> my-new-project
cd my-new-project
rm -rf .git

python -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt

cp .env.example .env
# edit .env, set a fresh DJANGO_SECRET_KEY

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# verify docs load
# http://127.0.0.1:8000/api/docs/

git init
git add .
git commit -m "Initial commit from Django base template"
```

Then start building: create your apps, models, serializers, views and API routes.

## Project structure

```
backend/
├── config/
│   ├── __init__.py          # loads Celery app
│   ├── api_urls.py          # API route registry for apps
│   ├── asgi.py
│   ├── celery.py
│   ├── urls.py              # root URL conf (admin, schema, docs)
│   ├── wsgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       └── production.py
├── apps/
│   ├── __init__.py
│   ├── common/              # reusable abstract models, permissions, utilities
│   └── users/               # custom User model
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── .env.example
├── .gitignore
├── manage.py
└── README.md
```