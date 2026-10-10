# Client-config (tashkilot imkoniyatlari) — dizayn

**Sana:** 2026-10-09
**Holat:** Dizayn (tasdiqlash kutilmoqda)

## 1. Maqsad

Platforma egasi har tashkilot uchun nimaga ruxsat berilishini belgilaydi:
- bo'limni (modulni) butunlay o'chirish — masalan materiallar sidebarda ko'rinmaydi
  va uning API'si yopiladi;
- amallarni cheklash — masalan tashkilot o'quvchilarni ko'radi, lekin qo'sha,
  tahrirlay yoki o'chira olmaydi (o'quvchilar tashqi manbadan, keyinchalik
  uzedu'dan keladi).

## 2. Hal qilingan qarorlar

| Mavzu | Qaror |
|---|---|
| Kim sozlaydi | Faqat platforma egasi (superuser). Direktor o'zgartira olmaydi |
| Format | `resource.action` imkoniyat kalitlari (`students.read`, `materials.read`, `students.update`) |
| Saqlash | Taqiqlangan kalitlar ro'yxati; qatori yo'q tashkilotda hammasi ochiq |
| Enforcement | Markaziy middleware (URL prefiks → resource, HTTP metod → action) |
| Frontend | Sidebar va tugmalar `can("x.y")` bilan yashiriladi; to'g'ridan URL → "yoqilmagan" sahifa |
| Frontend-only yashirish | Rad etilgan — API darajasida majburiy |

## 3. Imkoniyat modeli

**Resource** — tizim bo'limi. **Action** — `read`, `create`, `update`, `delete`.
Kalit: `<resource>.<action>`.

Qoidalar:
- `<resource>.read` taqiqlansa, o'sha resource'ning barcha amallari taqiqlanadi
  (ko'rinmaydigan narsani tahrirlab bo'lmaydi). Bu "modulni o'chirish".
- Default — hammasi ruxsat. Config faqat **taqiqlarni** saqlaydi, shuning uchun yangi
  resource qo'shilganda mavjud tashkilotlar avtomatik ruxsat oladi.

HTTP metod → action:
- `GET`, `HEAD`, `OPTIONS` → `read`
- `POST` → `create` (custom action'lar ham: masalan `POST /students/bulk-import/`)
- `PUT`, `PATCH` → `update`
- `DELETE` → `delete`

## 4. Resource registri (kodda, bitta manba)

`backend/apps/organizations/capabilities.py`:

```python
RESOURCES: dict[str, Resource]  # key -> Resource(label, api_prefixes)
```

Birinchi ro'yxat (API root'lar asosida):

| Resource | API prefikslar |
|---|---|
| `students` | `/api/students/` |
| `teachers` | `/api/teachers/` |
| `classes` | `/api/classes/` |
| `subjects` | `/api/subjects/` |
| `timetable` | `/api/timetable/`, `/api/timetable-slots/`, `/api/lessons/` |
| `attendance` | `/api/attendance/` |
| `materials` | `/api/materials/` |
| `tests` | `/api/tests/`, `/api/questions/`, `/api/question-pools/`, `/api/my-attempts/` |
| `activities` | `/api/activities/`, `/api/activity-submissions/`, `/api/my-activity-submissions/` |
| `tasks` | `/api/teacher-tasks/`, `/api/my-tasks/` |
| `games` | `/api/games/` |
| `duels` | `/api/duels/` |
| `gamification` | `/api/xp/`, `/api/streaks/`, `/api/achievements/`, `/api/leaderboard/`, `/api/league/`, `/api/weekly-goal/` |
| `remedial` | `/api/remedial-sessions/` |
| `reports` | `/api/reports/`, `/api/dashboard/` |

Hech qachon cheklanmaydi (registrda yo'q): `auth`, `users/me`, `organizations`,
`my-organizations`, `switch-organization`, `notifications`, `push`, `telegram`,
`school-config`, `class-access`, `school-day-exceptions`, `p` (public),
`demo-requests`, `options`, schema/docs, device bridge API.

Aniq prefiks ro'yxati implementatsiya rejasida `urls.py` fayllaridan tasdiqlanadi.

## 5. Ma'lumot modeli

`ClientConfig` (`apps.organizations`), `TimeStampedModel`:
- `organization` — OneToOne
- `denied` — JSON ro'yxat (`["materials.read", "students.create"]`); saqlashda
  registrga qarshi tekshiriladi (noma'lum kalit → ValidationError)

Servis:
- `get_denied(organization) -> frozenset[str]` — qator yo'q bo'lsa bo'sh to'plam.
  Kesh bilan (so'rov boshiga bitta query).
- `is_allowed(organization, key) -> bool` — `read` qoidasini hisobga oladi.

## 6. Backend enforcement

`CapabilityGateMiddleware` (`TenantMiddleware`'dan keyin):
1. `/api/` bo'lmagan yoki registrda yo'q yo'l → o'tkazadi.
2. Tashkilotni aniqlaydi: JWT `org_id` claim → tenant subdomain → `X-Organization-Id`
   (mavjud `OrganizationJWTAuthentication` bilan bir xil manba). Tashkilot
   aniqlanmasa → o'tkazadi (keyin view o'zi 401/403 beradi). **Hech qachon
   `objects.first()` ga tushmaydi.**
3. Kalit taqiqlangan → `403` mavjud error envelope'da:
   `{"error_code": "capability_denied", "detail": "...", "errors": {"capability": "<key>"}}`.

Superuser (platforma egasi) ham tashkilot ichida bo'lsa cheklovga bo'ysunadi;
config'ni u Django admin'da o'zgartiradi.

## 7. Frontend

- `GET /api/auth/me/` (`apps.users.auth_urls` → `MeView`) javobiga
  `capabilities: {"denied": [...]}` qo'shiladi.
- `useCan()` hook / `can(key)` helper — `read` qoidasini frontendda ham qo'llaydi.
- `DashboardLayout` nav item'lariga `requires?: "<resource>.read"`; taqiqlangan
  item ko'rinmaydi, bo'sh qolgan guruh ham yashiriladi.
- Route guard: taqiqlangan bo'limga URL bilan kirilsa "Bu bo'lim tashkilotingiz
  uchun yoqilmagan" sahifasi.
- Amal tugmalari (`students.create` — "O'quvchi qo'shish", import, tahrirlash,
  o'chirish) taqiqlangan bo'lsa ko'rsatilmaydi.
- API `403 capability_denied` qaytarsa — `getApiError` orqali tushunarli xabar.
- Tailwind `container` ishlatilmaydi.

## 8. Boshqaruv (platforma egasi)

Django admin: `Organization` sahifasida `ClientConfig` inline. `denied` uchun
resource × action checkbox jadvali (custom form widget). Saqlashda validatsiya.

## 9. Kelajak (uzedu)

Config tashkilot darajasida qoladi. Tuman/viloyat adminlari keyinchalik o'z
maktablari config'ini boshqarishi mumkin — model bunga to'sqinlik qilmaydi.
Registr yangi resource bilan kengayadi, mavjud tashkilotlar avtomatik ruxsat oladi.

## 10. Test

- Taqiqlangan `materials.read` → `/api/materials/` GET/POST 403; boshqa resource ishlaydi.
- `students.create` taqiqlangan → POST/bulk-import 403, GET 200.
- `students.read` taqiqlansa PATCH/DELETE ham 403.
- Org A config'i org B so'roviga ta'sir qilmaydi.
- Config qatori yo'q → hammasi ochiq.
- Registrda yo'q yo'l (`/api/auth/`, `/api/notifications/`) hech qachon bloklanmaydi.
- Noma'lum kalit saqlansa ValidationError.
- `/me` `capabilities.denied` qaytaradi.
- Frontend: nav filtri va `can()` (unit).

## 11. Tashqarida qoladi

- Rol bo'yicha farqlash (bir tashkilotda director'ga ruxsat, teacher'ga emas) — hozir
  yo'q; config butun tashkilotga tegishli.
- Direktor o'zi sozlashi — yo'q.
- `SchoolTimeLockMiddleware`'dagi `SchoolTimeSettings.objects.first()` fallback
  (boshqa maktab sozlamasini olishi mumkin) — alohida tuzatish sifatida qayd etildi.
