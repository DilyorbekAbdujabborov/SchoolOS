# Qurilma / Access-Control integratsiyasi — dizayn

**Sana:** 2026-10-09
**Holat:** Dizayn (tasdiqlash kutilmoqda)
**Birinchi qurilma:** Hikvision DS-K1T343MFWX (yuz tanish terminali)

## 1. Maqsad

Maktablardagi fizik access-control qurilmalari (birinchi bo'lib Hikvision yuz
terminali) SchoolOS bilan integratsiya qilinadi. Qurilma o'quvchi/xodim yuzini
tanigan event'ni SchoolOS'ga yetkazadi, SchoolOS esa yuz suratlarini va shaxs
yozuvlarini qurilmaga avtomatik yuklaydi (enrollment).

Natijalar:
- O'quvchining maktabga **kirish/chiqish** vaqti yoziladi (kunlik davomat).
- **Xodim** (o'qituvchi/direktor) davomati ham yoziladi.
- Kirish event'i o'sha vaqtdagi **darsga bog'lanib** `Attendance` (PRESENT/LATE)
  avtomatik belgilanadi.
- Kirish/chiqishda **xabar** yuboriladi.

## 2. Asosiy tamoyil: vendor-agnostik backend

Cloud backend **hech qanday vendor mantig'ini bilmaydi** — na ISAPI, na FDLib,
na Hikvision event JSON shakli. Cloud faqat normalizatsiyalangan kontrakt bilan
ishlaydi:

- normalizatsiyalangan **event** (kim, qachon, qaysi yo'nalish, qaysi qurilma);
- normalizatsiyalangan **buyruq** (shaxsni enroll/update/delete — osid, ism, surat).

Barcha vendorga xos kod faqat **bridge ichidagi driver**da yashaydi. Yangi
turdagi qurilma qo'shish = yangi driver klass yozish; cloud modellari, API va
davomat mantig'i **o'zgarmaydi** (ports & adapters namunasi).

## 3. Hal qilingan qarorlar

| Mavzu | Qaror |
|---|---|
| OSID kimga | Barcha `User` (student + o'qituvchi + xodim) |
| OSID format | 10 xonali raqamli string, global noyob, avtomatik |
| Enrollment | To'liq avtomatik: SchoolOS person + yuz suratini push qiladi |
| Topologiya | Har maktabda lokal **bridge** agent |
| Event transport | **A**: terminal → bridge (LAN push, real-time); bridge → cloud (HTTPS); buyruqlar uchun bridge cloud'ni poll qiladi |
| Cloud → maktab | Hech qachon kiruvchi ulanish yo'q; bridge faqat chiquvchi HTTPS |
| Ota-ona xabari | **Faza 1:** student o'z akkauntiga `notify()`. **Faza 2:** `parent_phone_number` ↔ Telegram bog'lanib, ota-onaga to'g'ridan |
| Vendor mantiq | Faqat bridge driverda; cloud agnostik |

## 4. Komponentlar

```
  TERMINAL (LAN)            BRIDGE (maktab mini-PC)              CLOUD (SchoolOS)
  Hikvision DS-K1T343MFWX   Python servis                       Django backend
  ─ yuz tanish             ─ HikvisionDriver (ISAPI/Digest)     ─ devices app
  ─ event POST ──LAN──────▶─ event listening host              ─ normalized API
  ─ ISAPI UserInfo/FDLib ◀──  normalize + batch  ──HTTPS POST──▶─ event ingest
                           ─ command poll         ──HTTPS GET──▶─ command queue
                           ─ driver.enroll() ◀──  ack           ─ attendance+notify
```

- **Terminal:** faqat LAN'da bridge bilan gaplashadi. Cloud bilan to'g'ridan
  aloqasi yo'q. Admin paroli faqat bridge config'ida.
- **Bridge:** org'ga bog'langan, token bilan autentifikatsiya qiladigan servis.
  Driver interfeysi orqali bir yoki bir nechta terminal bilan ishlaydi.
- **Cloud:** `devices` app — modellar, bridge API, davomatga ulash, xabar.

## 5. OSID dizayni

- `User.osid`: `CharField(max_length=10, unique=True, null=True)` (migration
  oralig'ida null, backfill'dan keyin to'ldiriladi).
- Generatsiya: 10 xonali, birinchi raqam 0 emas (`1000000000`–`9999999999`
  oralig'i). Tasodifiy + noyoblik tekshiruvi (collision bo'lsa qayta), yoki
  sekvens. Default: tasodifiy + `unique` constraint retry.
- Yangi `User` yaratilganda `save()` yoki signal orqali beriladi.
- **Backfill migration:** mavjud barcha `User`'ga osid beradi.
- StudentProfile'da takrorlanmaydi — `student.user.osid` orqali olinadi.
- Terminalda `employeeNoString = user.osid`.

## 6. Ma'lumot modeli (`apps/devices`)

Barcha model `TimeStampedModel`'dan meros, `organization` FK bilan (tenant
izolyatsiya mavjud namunaga mos: `save()` da org'ni to'ldirish).

### Bridge
Maktabdagi agent.
- `organization` FK
- `name` (masalan "1-maktab bridge")
- `token_hash` — bearer token hashi (ochiq token faqat yaratishda bir marta ko'rsatiladi)
- `last_seen_at`, `is_active`

### Device
Fizik qurilma. **Vendor-agnostik maydonlar.**
- `organization` FK, `bridge` FK
- `vendor` (masalan "hikvision"), `model`, `serial`
- `last_known_ip`
- `location_label` (masalan "Asosiy kirish")
- `direction` — `IN` / `OUT` / `BOTH` (bu qurilma qaysi yo'nalishni yozadi)
- `capabilities` — JSON (masalan `{"face_enroll": true, "card": false}`)
- `is_active`

### AccessEvent
Normalizatsiyalangan tanish event'i.
- `organization` FK, `device` FK
- `user` FK (null — agar osid topilmasa)
- `raw_osid` (qurilmadan kelgan employeeNo, debugging uchun)
- `event_time` (qurilma vaqti, UTC ga normalize)
- `direction` — `IN` / `OUT` / `UNKNOWN`
- `verify_mode` (masalan "face")
- `raw` — JSON (bridge yuborgan original payload, diagnostika)
- `dedup_key` — `unique` (`device_id` + qurilma event id/vaqt) — qayta ingest himoyasi

### DeviceCommand
Cloud → bridge buyruq navbati. **Normalizatsiyalangan.**
- `organization` FK, `device` FK
- `type` — `ENROLL` / `UPDATE` / `DELETE`
- `payload` — JSON (`osid`, `name`, `photo_url` qisqa-muddatli signed URL)
- `status` — `PENDING` / `SENT` / `DONE` / `FAILED`
- `attempts`, `result` (xato matni yoki natija)

### DailyAttendance
Kunlik kirish/chiqish (AccessEvent'lardan hosil).
- `organization` FK, `student` FK (`users.StudentProfile`), `date`
- `first_in_at`, `last_out_at`
- `status` — `PRESENT` / `LATE` / `ABSENT`
- `unique` (`student`, `date`)

### DeviceEnrollment (ixtiyoriy, per-user per-device holat)
- `device` FK, `user` FK, `status`, `last_command` FK, `synced_at`
- Kim qaysi qurilmaga yuklanganini kuzatadi.

## 7. Cloud API (bridge uchun; bearer token auth)

Hammasi `/api/devices/` ostida. Auth: `Authorization: Bearer <bridge-token>`;
token → `Bridge` → `organization`. Barcha so'rov shu org bilan chegaralanadi.

- `GET /api/devices/commands/`
  Kutilayotgan `DeviceCommand`'lar (PENDING). `SENT` deb belgilanadi.
  Javob: `[{id, type, device_serial, payload:{osid,name,photo_url}}]`
- `POST /api/devices/commands/<id>/ack/`
  Tana: `{status: "DONE"|"FAILED", result: "..."}`. `DeviceEnrollment`
  yangilanadi.
- `POST /api/devices/events/`
  Tana (batch): `[{device_serial, osid, event_time, direction, verify_mode, raw}]`.
  Dedup → `AccessEvent` → davomat → xabar. Javob: qabul qilingan/rad etilgan id'lar.
- `POST /api/devices/heartbeat/`
  Tana: `{device_serials:[...]}`. `Bridge.last_seen_at`, `Device.last_known_ip`.

Tenant qoidasi: event'dagi `osid` bu org'ga tegishli `User`'niki bo'lishi shart;
boshqa org osid'i → event `user=None` bilan saqlanadi yoki rad etiladi (log).

## 8. Enrollment oqimi (to'liq avtomatik)

1. `User` yaratiladi / `avatar` o'zgaradi / student org'ga qo'shiladi → service
   o'sha org'ning har active `Device`'i uchun `DeviceCommand(ENROLL)` yaratadi.
   `payload = {osid, name, photo_url}` (photo = `User.avatar`, qisqa-muddatli
   signed URL).
2. Bridge `GET /commands/` bilan oladi.
3. Driver qurilmaga yozadi (Hikvision misoli): person yozuvi (employeeNo=osid,
   ism), so'ng yuz surati.
4. Bridge `POST /commands/<id>/ack/` bilan natijani qaytaradi.
5. Cloud `DeviceEnrollment` holatini yangilaydi. FAILED bo'lsa retry (attempts).

Avatar yo'q bo'lsa: person yozuvi push qilinadi, yuz "kutilmoqda" holatida
qoladi (yoki admin terminalda oladi). UI'da ko'rsatiladi.

## 9. Event → davomat oqimi

1. Terminal yuzni taniydi → LAN'da bridge'ga event POST.
2. Bridge normalize qiladi (osid, UTC vaqt, direction) va batch qilib
   `POST /events/`.
3. Cloud:
   - `dedup_key` bo'yicha takror event tashlanadi;
   - `raw_osid` → `User` (org ichida);
   - `AccessEvent` saqlanadi;
   - **DailyAttendance** yangilanadi: `IN` → `first_in_at` (bo'sh bo'lsa),
     `OUT` → `last_out_at`;
   - **status**: `first_in_at` ≤ `SchoolTimeSettings.start_time` + grace → PRESENT,
     aks holda LATE. Grace default 5 daqiqa (sozlanadi). Smena bo'lsa
     `SchoolTimeSettings` smena vaqtidan foydalanadi;
   - **darsga ulash (Faza 3):** event vaqtidagi/keyingi `Lesson` topiladi,
     `Attendance` PRESENT/LATE yaratiladi/yangilanadi (mavjud unique constraint
     `lesson+student`);
   - **xabar:** IN/OUT da student akkauntiga `notify(...)` (Faza 1).

## 10. Xabar

`notify(recipient, title, body, category)` — mavjud yagona kirish nuqtasi
(Telegram + web push). Faza 1: `recipient = student.user`. Faza 2: ota-ona
`parent_phone_number` ↔ Telegram chat bog'lanishi qo'shilib, ota-onaga
to'g'ridan yuboriladi. Yangi `Notification.Category` qiymati qo'shilishi mumkin
(masalan `ATTENDANCE`).

## 11. Bridge paketi

- Repo ichida `bridge/` — mustaqil Python servis.
- **Driver interfeysi** (port): `DeviceDriver` abstrakt — `fetch_events()`
  (yoki listening-host callback), `enroll(person)`, `update(person)`,
  `delete(osid)`, `capabilities`.
- **HikvisionDriver** (adapter): ISAPI, HTTP Digest auth (realm biz ko'rganimiz
  `DS-...`), `UserInfo/Record`, `FDLib/FaceDataRecord`, event listening host yoki
  `AcsEvent` poll.
- Config fayli: `cloud_base_url`, `bridge_token`, terminal(lar) `ip`,
  `admin_user`, `admin_password`, `direction` mapping. **Parollar faqat
  bridge'da.**
- Ishga tushirish: Docker yoki systemd (maktab mini-PC/Raspberry Pi).
- Event listening: terminal "HTTP listening host" bridge IP:portiga POST qiladi;
  tarmoqda ishlamasa — `AcsEvent` poll fallback (yondashuv B).

## 12. Xavfsizlik

- Per-bridge bearer token, org'ga bog'liq, bekor qilinadigan, DB'da hashlangan.
- Event endpoint boshqa org osid'ini qabul qilmaydi (tenant izolyatsiya testi).
- Yuz surati faqat qisqa-muddatli signed URL orqali (doimiy ochiq URL emas).
- Barcha trafik HTTPS; bridge faqat chiquvchi — maktabga kiruvchi port yo'q.
- Payload hajmi va rate limit event endpoint'da.
- Terminal admin paroli cloud'da hech qachon saqlanmaydi.

## 13. Fazalar

- **P1:** `User.osid` + backfill; `devices` modellar; event ingest API + bridge
  skeleti (poll); `DailyAttendance`; student xabari; tenant izolyatsiya.
- **P2:** to'liq enrollment push (person + yuz), command navbati + ack, retry;
  listening-host real-time event.
- **P3:** darsga avto-ulash (`Attendance` PRESENT/LATE); ota-ona Telegram xabari.

## 14. Test

- OSID: generatsiya, 10-xonalik, noyoblik/collision retry, backfill.
- Event ingest: dedup, `raw_osid`→user, noma'lum osid (`user=None`).
- Davomat: PRESENT vs LATE (`SchoolTimeSettings` + grace), smena, IN/OUT
  first_in/last_out.
- Command lifecycle: ENROLL yaratilishi, poll, ack DONE/FAILED, retry.
- **Tenant izolyatsiya:** org A bridge tokeni org B osid event'ini / command'ini
  ololmaydi/yubora olmaydi.
- Bridge: `HikvisionDriver` ISAPI chaqiruvlari yozib olingan fixture'lar bilan;
  event normalizatsiya; driver interfeysi kontrakt testi (soxta driver).
- Xabar: IN/OUT da `notify` chaqirilishi.

## 15. Taxminlar / ochiq masalalar

- **Taxmin:** event transport A (terminal→bridge push). Ba'zi tarmoqda listening
  host ishlamasa, B (poll) ga tushamiz — driver ikkalasini qo'llaydi.
- **Taxmin:** ota-ona Faza 1 da student akkauntidan xabar oladi.
- **Ochiq:** bitta terminal IN va OUT ni ham beradimi (event'dagi yo'nalish
  maydoni), yoki kirish/chiqish uchun alohida qurilma? Model ikkalasini qo'llaydi
  (`Device.direction`), lekin maktabdagi real sozlama tasdiqlanishi kerak.
- **Ochiq:** OSID generatsiya tasodifiy-retry yoki sekvens — default
  tasodifiy-retry.
- **Ochiq:** grace (kech qolish) daqiqasi `SchoolTimeSettings`'ga sozlama
  sifatida qo'shiladimi yoki global constant — default 5 daqiqa, keyin sozlama.
