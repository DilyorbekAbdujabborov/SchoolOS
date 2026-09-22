# SchoolOS — serverga chiqarish

Bu loyiha endi Docker orqali bitta buyruq bilan ishga tushadigan holatga keltirildi:
Postgres, Redis, Django (gunicorn), Celery worker, Celery beat, Telegram bot va
frontend (Caddy orqali, avtomatik HTTPS bilan) — hammasi bitta `docker compose up`
bilan ko'tariladi.

## Sizga kerak bo'ladigan narsalar (bularni men siz uchun qila olmayman)

1. **Server (VPS).** Islgan provayderdan (masalan Hetzner, DigitalOcean, Timeweb va h.k.)
   kamida 2 GB RAM'li Ubuntu server sotib oling.
2. **Domen.** Domeningizning DNS sozlamalarida **A record**'ni shu server IP-manziliga
   yo'naltiring (masalan `maktab.uz` → `1.2.3.4`). HTTPS avtomatik ishlashi uchun bu shart.
3. Serverda **Docker** va **Docker Compose** o'rnatilgan bo'lishi kerak:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```

Bulardan keyingisini men (yoki siz) serverning o'zida bajaramiz.

## O'rnatish qadamlari

1. Loyihani serverga ko'chiring (git clone yoki fayllarni yuklab):
   ```bash
   git clone <repo-url> schoolos && cd schoolos
   ```

2. Compose darajasidagi sozlamalar:
   ```bash
   cp .env.example .env
   ```
   `.env` faylini oching va to'ldiring:
   - `DOMAIN` — haqiqiy domeningiz (masalan `maktab.uz`). Localhost'da sinash uchun shu
     qiymatni o'zgartirmasangiz ham bo'ladi.
   - `DJANGO_DB_PASSWORD` — haqiqiy, kuchli parol qo'ying (yuqoridagi placeholder emas).

3. Backend sozlamalari:
   ```bash
   cp backend/.env.example backend/.env
   ```
   `backend/.env` faylini oching va **albatta** quyidagilarni o'zgartiring:
   - `DJANGO_SECRET_KEY` — yangi, tasodifiy qiymat qo'ying (masalan:
     `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`).
   - `DJANGO_DEBUG=False`
   - `DJANGO_ALLOWED_HOSTS=maktab.uz` (o'z domeningiz)
   - Telegram bot, Gemini, Groq kalitlari — mavjud lokal qiymatlaringizni ko'chirsangiz
     bo'ladi, yoki productionga alohida kalitlar olishingiz mumkin.

   `DJANGO_DB_*` va `CELERY_*`/`REDIS_URL` qatorlarini **backend/.env**'da o'zgartirmang —
   ular `docker-compose.yml` tomonidan avtomatik, to'g'ri qiymatlar bilan almashtiriladi
   (Postgres/Redis konteynerlariga ishora qiladi).

4. Ishga tushiring:
   ```bash
   docker compose up -d --build
   ```
   Birinchi marta ishga tushirilganda backend migratsiyalarni va statik fayllarni
   avtomatik tayyorlaydi (`entrypoint.sh`). Bir necha soniya kuting, keyin:
   ```bash
   docker compose ps
   ```
   bilan hammasi "running/healthy" ekanini tekshiring.

5. Birinchi direktor (superuser) hisobini yarating:
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

6. Brauzerda `https://maktab.uz` (yoki tanlagan domeningiz) ochilishi kerak — Caddy
   HTTPS sertifikatini Let's Encrypt'dan avtomatik oladi, hech narsa qo'lda sozlash
   shart emas.

## Yangilash (keyingi deploylar uchun)

```bash
git pull
docker compose up -d --build
```

## Zaxira nusxa (backup)

Ma'lumotlar bazasi `db_data` nomli Docker volume'da saqlanadi. Uni zaxiralash uchun:

```bash
docker compose exec db pg_dump -U schoolos schoolos > backup.sql
```

## Muhim eslatma

`.env` va `backend/.env` fayllarini **hech qachon** git'ga qo'shmang — ular allaqachon
`.gitignore`'da. Production'dagi maxfiy kalitlar faqat serverning o'zida, shu fayllarda
turishi kerak.
