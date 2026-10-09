# Client-config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Per-organization capability config (`resource.action` deny-list) set by the platform owner, enforced on the API and reflected in the frontend sidebar, routes and action buttons.

**Architecture:** A code registry (`apps/organizations/capabilities.py`) maps resources to API path prefixes. `ClientConfig` (OneToOne with `Organization`) stores denied keys. Enforcement runs at the end of `OrganizationHeaderAuthentication.authenticate`, where the acting organization is final — no second org resolution. `MeSerializer` exposes `capabilities.denied`; the frontend `can()` helper filters nav, guards routes and hides buttons.

**Tech Stack:** Django/DRF backend, React + TypeScript + Tailwind frontend.

**Spec:** `docs/superpowers/specs/2026-10-09-client-config-design.md`

## Global Constraints

- Keys are `<resource>.<action>`, actions `read|create|update|delete`; denying `read` denies every action on that resource.
- Method → action: GET/HEAD/OPTIONS→read, POST→create, PUT/PATCH→update, DELETE→delete.
- Denied → HTTP 403, envelope `error_code: "capability_denied"`, `errors: {"capability": ["<key>"]}`.
- No config row → everything allowed. Unknown key on save → ValidationError.
- Paths not in the registry are never gated.
- Only superusers edit config (Django admin).
- No Tailwind `container` class.

## Review Focus

- Org A's denials never affect org B's requests (test in Task 2).
- `X-Organization-Id` / subdomain switching to another org applies *that* org's config (test in Task 2).
- Prefix matching must not over-match (`/api/tests/` vs `/api/teacher-tasks/`; `/api/xp/` vs `/api/xp-something/`) — match on whole path segment (test in Task 1).
- Unauthenticated requests to gated paths still get 401, not 403 capability (test in Task 2).
- `read` denial hides writes too (test in Task 1).

### Task 1: Registry, `ClientConfig`, services, admin
Files: create `apps/organizations/capabilities.py`; modify `apps/organizations/models.py`, `admin.py`; test `apps/organizations/test_capabilities.py`.
Produces: `RESOURCES: dict[str, Resource]`, `ACTIONS`, `all_keys() -> list[str]`, `capability_for(path: str, method: str) -> str | None`, `ClientConfig(organization, denied: list[str])` with `clean()`, `get_denied(org) -> frozenset[str]`, `is_allowed(denied: frozenset, key: str) -> bool`.
- [ ] RED tests: segment-exact prefix match, method mapping, unregistered path → None, read-denial implies writes, unknown key ValidationError, no row → empty set.
- [ ] Implement; migration; admin inline with checkbox grid form.
- [ ] GREEN, commit.

### Task 2: Enforcement in auth layer
Files: modify `apps/organizations/authentication.py`; test `apps/organizations/test_capabilities.py`.
Consumes Task 1. Produces `CapabilityDenied(AppError)` (403, code `capability_denied`).
- [ ] RED API tests: denied materials.read → GET/POST /api/materials/ 403 with error_code; students.create denied → POST 403, GET 200; other org unaffected; header switch applies target org config; unregistered route (/api/auth/me/) untouched; anonymous → 401.
- [ ] Call gate at end of `OrganizationHeaderAuthentication.authenticate` when `request.organization` set.
- [ ] GREEN, full suite, commit.

### Task 3: `/api/auth/me/` exposes capabilities
Files: modify `apps/users/serializers.py` (MeSerializer `capabilities`); test in `apps/organizations/test_capabilities.py`.
- [ ] RED: me returns `capabilities.denied` sorted list for acting org; empty when none.
- [ ] Implement via `request.organization` from serializer context (fallback `user.active_organization`).
- [ ] GREEN, commit.

### Task 4: Frontend gating
Files: `src/types/index.ts` (User.capabilities), new `src/lib/capabilities.ts` (`can(user, key)`), nav definitions (`requires`), `DashboardLayout.tsx` filter, route guard + `FeatureDisabledPage`, students page buttons.
- [ ] Unit-level: `can()` read-implies rule (vitest if present, else typecheck + manual).
- [ ] `npm run build` (tsc) passes.
- [ ] Commit.
