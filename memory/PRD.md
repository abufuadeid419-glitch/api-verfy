# Smart System (النظام الذكي) — Mobile (Expo) PRD

## Original problem
"clone this mobile app: https://github.com/abufuadeid419-glitch/number-verifications.git"

## User choices (this clone session, 2026-06)
- Full clone — all 4 roles (Developer, Owner, Accountant, Field Agent) and all screens.
- Login: phone + OTP via the user's own Bird account (key provided); keep the original flow.
- Database: connect to the user's EXISTING Convex deployment `fearless-ostrich-878`
  (URL + deploy key provided) with its real data — do NOT wipe/reseed.
- Arabic RTL (like the original).
- Developer (super-admin) phone +963984644375 — must NOT appear in the codebase
  (stored only in Convex env var `DEVELOPER_PHONES`).

## What this app is
Arabic RTL sales & distribution ERP. Roles: DEVELOPER, OWNER, ACCOUNTANT, FIELD_AGENT (distributor).
Auth: phone number + 6-digit OTP (Bird SMS, WhatsApp fallback). 30-day bearer sessions.
Activation by license code (LIC-), employee code (EMP-), or a self-service trial.

## Architecture (as restored on this platform)
- Backend + DB: **Convex** (external, user-managed deployment `fearless-ostrich-878`).
  The entire REST surface (`/api/...`) is served by `convex/http.ts` from the deployment's
  `.site` domain; all data, auth, OTP and file (logo) storage live in Convex.
  `convex/` source: schema.ts, lib.ts, edge.ts (auth/OTP/logo), extra.ts (dev console + misc),
  products/customers/sales/collections/returns/deliveries/employees/tracking/stats/
  notifications/routes/vouchers/purchases/targets/crons.
- FastAPI (`backend/server.py`) is a DB-less stub kept only so the platform supervisor has a
  healthy backend service; the app does not use it.
- Frontend: Expo Router. `src/api.ts` calls `EXPO_PUBLIC_CONVEX_SITE_URL/api{path}`. Root gate in
  `app/_layout.tsx` routes to login / consent / activate / blocked / dev / owner / acct / dist.
  Role tab groups via `src/RoleTabs.tsx`. UI kit `src/ui.tsx`. Cairo font, moss-green theme, forced RTL.
- Env:
  - frontend/.env: EXPO_PUBLIC_CONVEX_URL, EXPO_PUBLIC_CONVEX_SITE_URL (+ protected packager vars).
  - backend/.env: CONVEX_URL, CONVEX_DEPLOY_KEY (secret; server-side only).
  - Convex deployment env: BIRD_API_KEY, BIRD_BASE_URL, BIRD_WHATSAPP_LANGUAGE, DEVELOPER_PHONES,
    OTP_PEPPER (all already set on `fearless-ostrich-878`).

## Clone / restore done (2026-06, this session)
- Copied the full repo frontend (app/, src/, convex/, constants/, assets/, scripts/, app.json,
  package.json, tsconfig) and the backend stub into /app; preserved protected .env packager vars.
- Pointed frontend at the live Convex deployment; `yarn install` (adds `convex` client etc).
- Verified the deployment is live and fully configured (Bird key, DEVELOPER_PHONES=+963984644375,
  OTP_PEPPER all present via `npx convex env list`).
- Verified end-to-end:
  - Convex HTTP root `GET /api/` → "Smart System API (Convex)"; `GET /api/auth/me` (no token) → 401.
  - `POST /api/auth/otp/request` (bad phone) → Arabic 400; `/auth/otp/verify` (no request) → Arabic error.
  - Login screen renders (Arabic RTL, +963 default, warehouse hero).
  - Seeded isolated test org `org_test_1` (edge:seedTestAccounts); owner dashboard renders live
    (KPIs, onboarding, alerts, bottom tabs) with `test_token_owner`. Dev/acct/agent tokens auth OK.

## Feature set (inherited, all implemented in Convex)
- Developer: stats, licenses, orgs (extend/suspend/reactivate), plans, payment settings, upgrade
  approvals, app-version/update gate, monitoring, deletion review.
- Owner: KPIs, low-stock alerts, agent performance + leaderboard, products CRUD, purchases,
  deliveries, employees (invite by code), org profile/logo, GPS agent map, route planner,
  customer price lists, reports, sales targets, trial countdown, Pro upsell.
- Distributor (field agent): own inventory, new sale (cash/credit, discounts), collections,
  sales/warehouse returns, payment vouchers, customers CRUD, today's route, offline-first sync,
  PDF/80mm Bluetooth receipts, WhatsApp debt reminders.
- Accountant: overview, invoices/collections/returns, debts with collect, customer statements.
- Blocked screen for suspended/expired orgs; consent gate; legal screens.

## Known constraints
- OTP login sends real (paid) Bird SMS/WhatsApp → cannot be automated; validated via seeded tokens.
- Bluetooth thermal printing & background GPS require a native build (not Expo Go / web preview).
- Maps render on native devices; web preview shows list fallbacks.

## Backlog / next (P1/P2)
- P1: seed a demo org with sample products/customers/sales for quick exploration (on request).
- P1: review SMS deliverability to Syria in the Bird workspace (external; WhatsApp is the working path).
- P2: push notifications (Emergent managed) — needs google-services.json + a native build.
