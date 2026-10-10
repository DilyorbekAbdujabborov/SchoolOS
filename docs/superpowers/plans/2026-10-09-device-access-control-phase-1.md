# Device Access-Control — Phase 1 (cloud foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the vendor-agnostic cloud foundation that lets a school bridge authenticate, push normalized face-terminal events, and have them become per-day attendance with a notification — all testable without a physical terminal.

**Architecture:** New `apps.devices` Django app holds `Bridge`, `Device`, `AccessEvent`, `DailyAttendance`. A `BridgeTokenAuthentication` class resolves a bearer token to its `Bridge` and sets `request.organization`, mirroring the existing `OrganizationJWTAuthentication` pattern. An `ingest_events` service deduplicates, resolves `osid → User`, writes the `AccessEvent`, updates `DailyAttendance` (PRESENT/LATE from `SchoolTimeSettings`), and notifies the student. All vendor specifics stay out of the cloud — the API speaks a normalized contract only.

**Tech Stack:** Django, Django REST Framework, SimpleJWT (existing), PostgreSQL (prod) / SQLite (dev). Tests: Django `TestCase`/`APITestCase` with `apps.common.testing` factories.

**Spec:** `docs/superpowers/specs/2026-10-09-device-access-control-integration-design.md`

## Global Constraints

- Every new model subclasses `apps.common.models.TimeStampedModel` and carries an `organization` FK, filling it in `save()` when derivable (follow `apps.attendance.models.Attendance`).
- OSID is a 10-digit numeric string, first digit non-zero, globally unique (`User.osid`).
- All user-facing strings wrapped in `gettext_lazy as _` (project convention).
- Bridge endpoints authenticate by bridge token only — never user JWT / `X-Organization-Id`. Cross-organization data must never be reachable with a bridge token.
- Phase 1 excludes enrollment push and `DeviceCommand` (Phase 2) and lesson-linked `Attendance` + parent Telegram (Phase 3).
- Register the new app in `backend/config/settings/base.py` `INSTALLED_APPS` and its urls in `backend/config/api_urls.py`.
- **Forward-compat (uzedu / district-region):** every device record stays scoped to `organization` (the school). A future district (tuman) / region (viloyat) hierarchy and its roles sit *above* `organization` and aggregate through it — so no district/region FK is added to device models now, and the aggregation base stays `organization`. `User.osid` is deliberately **global**-unique (not org-scoped) so it can serve as the stable identifier across a national system. Do not add role checks that assume the role set is only director/teacher/student.

## Review Focus

- **Unknown / cross-org osid in an event:** an event whose `osid` matches no `User` in the bridge's org is stored with `user=None` (not dropped, not matched to another org's user). Test in Task 5.
- **Duplicate event replay:** the same terminal event posted twice (bridge retry) creates exactly one `AccessEvent` and does not double-update `DailyAttendance`. Test in Task 4.
- **No `SchoolTimeSettings` for the org:** attendance ingest must not crash; it falls back to PRESENT (no late threshold known). Test in Task 4.
- **Revoked / malformed bridge token:** a disabled `Bridge` or a token not matching any hash is rejected 401, never silently treated as anonymous-but-allowed. Test in Task 3.
- **OSID collision on generation:** the generator retries on the unique constraint and never returns a duplicate or a leading-zero value. Test in Task 1.

---

### Task 1: `User.osid` field, generator, and backfill

**Files:**
- Modify: `backend/apps/users/models.py` (add `osid` field + generation hook)
- Create: `backend/apps/users/services.py` (or extend if present) — `generate_osid()`
- Modify: migration dir `backend/apps/users/migrations/` (schema + data backfill)
- Test: `backend/apps/users/tests.py` (or a focused `test_osid.py`)

**Interfaces:**
- Produces: `User.osid` (`str`, 10 digits, unique, nullable at DB level); `generate_osid() -> str`; `User` gets a non-null `osid` on create.

- [ ] **Step 1: Write failing tests**

```python
def test_generate_osid_is_10_digits_no_leading_zero():
    osid = generate_osid()
    assert len(osid) == 10 and osid.isdigit() and osid[0] != "0"

def test_new_user_gets_unique_osid():
    a = make_student()[0]; b = make_student()[0]
    assert a.osid and b.osid and a.osid != b.osid

def test_generate_osid_retries_on_collision(monkeypatch):
    # force the first candidate to equal an existing osid, expect a different final value
    ...
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `cd backend && python manage.py test apps.users -v 2`
Expected: FAIL (`osid` attribute / `generate_osid` missing).

- [ ] **Step 3: Implement `generate_osid() -> str` and the field**

Add `osid = models.CharField(max_length=10, unique=True, null=True, blank=True)` to `User`. `generate_osid()` draws a random 10-digit value in `1000000000`–`9999999999` and re-draws while `User.objects.filter(osid=...).exists()`. Assign in `User.save()` when `self.osid is None` (retry on `IntegrityError` for the race).

- [ ] **Step 4: Create schema migration + data migration**

`python manage.py makemigrations users`, then add a data migration that calls the generator for every existing `User` with `osid IS NULL` (iterate, save). Keep field nullable (no NOT NULL in Phase 1).

- [ ] **Step 5: Run tests, verify pass**

Run: `cd backend && python manage.py test apps.users -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/apps/users/
git commit -m "feat(users): add unique 10-digit osid with backfill"
```

---

### Task 2: `apps.devices` app with `Bridge` and `Device` models

**Files:**
- Create: `backend/apps/devices/__init__.py`, `apps.py`, `models.py`, `admin.py`
- Modify: `backend/config/settings/base.py` (INSTALLED_APPS: `"apps.devices"`)
- Test: `backend/apps/devices/tests.py`

**Interfaces:**
- Produces: `Bridge(organization, name, token_hash, last_seen_at, is_active)`; `Device(organization, bridge, vendor, model, serial, last_known_ip, location_label, direction, capabilities, is_active)`; `Device.Direction` choices `IN/OUT/BOTH`; `Bridge.issue_token() -> str` (sets `token_hash`, returns the one-time plaintext).

- [ ] **Step 1: Write failing tests**

```python
def test_issue_token_sets_hash_and_returns_plaintext():
    b = Bridge.objects.create(organization=default_organization(), name="b1")
    token = b.issue_token()
    assert token and b.token_hash and b.token_hash != token

def test_device_belongs_to_bridge_org():
    ...  # Device.save() fills organization from bridge when omitted
```

- [ ] **Step 2: Run tests, verify fail**

Run: `cd backend && python manage.py test apps.devices -v 2`
Expected: FAIL (app/models missing).

- [ ] **Step 3: Implement the app and models**

Create the app (`apps.py` `name = "apps.devices"`). Models subclass `TimeStampedModel`. `issue_token()` generates a random URL-safe token (`secrets.token_urlsafe(32)`), stores `make_password(token)` (Django hasher) in `token_hash`, returns the plaintext. `Device.save()` fills `organization_id` from `bridge.organization_id` when unset. Register both in `admin.py`. Add `"apps.devices"` to INSTALLED_APPS.

- [ ] **Step 4: Make migrations, run tests**

Run: `cd backend && python manage.py makemigrations devices && python manage.py test apps.devices -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/devices/ backend/config/settings/base.py
git commit -m "feat(devices): add Bridge and Device models"
```

---

### Task 3: `BridgeTokenAuthentication` and `IsBridge` permission

**Files:**
- Create: `backend/apps/devices/authentication.py`, `backend/apps/devices/permissions.py`
- Test: `backend/apps/devices/tests.py`

**Interfaces:**
- Consumes: `Bridge.token_hash` (Task 2).
- Produces: `BridgeTokenAuthentication` (DRF auth class) setting `request.bridge` and `request.organization`; `IsBridge` permission (`request.bridge is not None`). Verification uses Django's `check_password(token, bridge.token_hash)` directly — no extra method on `Bridge`.

- [ ] **Step 1: Write failing tests**

```python
def test_valid_token_resolves_bridge_and_org():
    # request with Authorization: Bearer <token> → request.bridge, request.organization set
def test_revoked_bridge_rejected_401():
    # is_active=False → AuthenticationFailed
def test_unknown_token_rejected_401():
    # random token matches no hash → AuthenticationFailed
```

- [ ] **Step 2: Run tests, verify fail**

Run: `cd backend && python manage.py test apps.devices -v 2`
Expected: FAIL.

- [ ] **Step 3: Implement auth + permission**

`BridgeTokenAuthentication.authenticate(request)` reads the `Bearer` token, iterates active `Bridge` rows and `check_password(token, b.token_hash)` (or store a fast lookup prefix if needed later), on match sets `request.bridge = bridge`, `request.organization = bridge.organization`, bumps nothing here, and returns `(bridge, None)`; no `Bearer` header → return `None`; malformed/`is_active=False`/no match → raise `exceptions.AuthenticationFailed`. `IsBridge.has_permission` returns `getattr(request, "bridge", None) is not None`.

- [ ] **Step 4: Run tests, verify pass**

Run: `cd backend && python manage.py test apps.devices -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/devices/
git commit -m "feat(devices): bridge-token authentication and permission"
```

---

### Task 4: `AccessEvent`, `DailyAttendance`, and the `ingest_events` service

**Files:**
- Modify: `backend/apps/devices/models.py` (`AccessEvent`, `DailyAttendance`)
- Create: `backend/apps/devices/services.py` (`ingest_events`)
- Test: `backend/apps/devices/tests.py`

**Interfaces:**
- Consumes: `Device` (Task 2); `User.osid` (Task 1); `apps.school_config.models.SchoolTimeSettings`; `apps.notifications.services.notify`.
- Produces: `AccessEvent(organization, device, user, raw_osid, event_time, direction, verify_mode, raw, dedup_key)` with `dedup_key` unique; `DailyAttendance(organization, student, date, first_in_at, last_out_at, status)` unique on `(student, date)`; `ingest_events(bridge, items: list[dict]) -> dict` returning `{"accepted": [...], "duplicate": [...], "unmatched": [...]}`.

Each `item`: `{"device_serial", "osid", "event_time" (ISO), "direction" (IN/OUT/UNKNOWN), "verify_mode", "raw"}`.

- [ ] **Step 1: Write failing tests**

```python
def test_in_event_creates_access_event_and_daily_attendance():
    # PRESENT when first_in <= school start + grace
def test_late_when_first_in_after_grace():
    # SchoolTimeSettings start 08:00, event 08:30 → LATE
def test_missing_school_time_settings_defaults_present():
    # no SchoolTimeSettings row → PRESENT, no crash
def test_duplicate_dedup_key_ingested_once():
    # same item twice → one AccessEvent, DailyAttendance unchanged on 2nd
def test_unknown_osid_stored_with_user_none():
    # osid not in org → AccessEvent.user is None, reported as unmatched
def test_in_event_notifies_student():
    # Notification created for student.user
```

- [ ] **Step 2: Run tests, verify fail**

Run: `cd backend && python manage.py test apps.devices -v 2`
Expected: FAIL.

- [ ] **Step 3: Implement models + `ingest_events`**

`dedup_key = f"{device.id}:{item['event_time']}:{item['osid']}"`. For each item: resolve `Device` by serial within `bridge.organization`; `User.objects.filter(osid=..., ...).first()` scoped to the org (via membership); create `AccessEvent` (skip on existing `dedup_key`). When the user has a `StudentProfile` and direction is `IN`/`OUT`, upsert `DailyAttendance` for `event_time.date()`: set `first_in_at` if empty (IN), `last_out_at` (OUT); status PRESENT if `SchoolTimeSettings` absent or `first_in_at.time() <= start_time + GRACE`, else LATE. `GRACE = timedelta(minutes=5)` module constant. On IN/OUT call `notify(recipient=student.user, title=..., body=..., category=Notification.Category.GENERAL)`. Return the accepted/duplicate/unmatched buckets.

- [ ] **Step 4: Make migrations, run tests**

Run: `cd backend && python manage.py makemigrations devices && python manage.py test apps.devices -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/devices/
git commit -m "feat(devices): access-event ingest into daily attendance with notify"
```

---

### Task 5: Bridge API endpoints (`events`, `heartbeat`) + tenant isolation

**Files:**
- Create: `backend/apps/devices/serializers.py`, `backend/apps/devices/views.py`, `backend/apps/devices/urls.py`
- Modify: `backend/config/api_urls.py` (`path("", include("apps.devices.urls"))`)
- Test: `backend/apps/devices/tests.py`

**Interfaces:**
- Consumes: `ingest_events` (Task 4); `BridgeTokenAuthentication`, `IsBridge` (Task 3).
- Produces: `POST /api/devices/events/` (batch ingest, returns the buckets dict); `POST /api/devices/heartbeat/` (`{"device_serials": [...]}` → updates `Bridge.last_seen_at` and `Device.last_known_ip` from `REMOTE_ADDR`, returns `204`). Both use only `BridgeTokenAuthentication` + `IsBridge`.

- [ ] **Step 1: Write failing tests**

```python
def test_post_events_with_bridge_token_ingests():
    # 200, AccessEvent created, body has accepted ids
def test_post_events_without_token_401():
def test_bridge_cannot_post_osid_of_another_org():
    # osid belongs to org B; bridge for org A → event stored user=None (unmatched), never matched to B
def test_heartbeat_updates_last_seen():
```

- [ ] **Step 2: Run tests, verify fail**

Run: `cd backend && python manage.py test apps.devices -v 2`
Expected: FAIL.

- [ ] **Step 3: Implement serializers, views, urls**

`EventItemSerializer` validates one item (fields from Task 4). `EventsView`/`HeartbeatView` are DRF `APIView`s with `authentication_classes = [BridgeTokenAuthentication]`, `permission_classes = [IsBridge]`. `EventsView.post` validates the list, calls `ingest_events(request.bridge, data)`, returns the buckets. `HeartbeatView.post` sets `request.bridge.last_seen_at = now()` and updates matching `Device.last_known_ip`. Wire `urls.py` and register in `config/api_urls.py`.

- [ ] **Step 4: Run tests, verify pass**

Run: `cd backend && python manage.py test apps.devices -v 2`
Expected: PASS.

- [ ] **Step 5: Run the whole backend suite**

Run: `cd backend && python manage.py test -v 1`
Expected: PASS (no regressions, esp. users/organizations tenant tests).

- [ ] **Step 6: Commit**

```bash
git add backend/apps/devices/ backend/config/api_urls.py
git commit -m "feat(devices): bridge events and heartbeat endpoints"
```

---

## Phase 1 exit criteria

A bridge token authenticates; `POST /api/devices/events/` turns normalized IN/OUT events into `AccessEvent` + `DailyAttendance` (PRESENT/LATE) and notifies the student; duplicates and unknown/cross-org osids are handled safely; heartbeat records liveness. No terminal required — all proven by the test suite.

**Next plans (not in this document):**
- **Phase 2:** `DeviceCommand` queue + `GET /commands/` + `ack`; the `bridge/` Python service with the `DeviceDriver` port and `HikvisionDriver` adapter (ISAPI/Digest, `UserInfo/Record`, `FDLib/FaceDataRecord`); enrollment command generation on user create / avatar change; signed short-lived photo URLs.
- **Phase 3:** lesson-linked `Attendance` (PRESENT/LATE against the timetable); `parent_phone_number ↔ Telegram` linkage for direct parent notification; staff-attendance reporting in the dashboard.
