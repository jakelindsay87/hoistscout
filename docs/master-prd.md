# HoistScraper v0.1 – Master Product Requirements Document (PRD)

## 0. Executive Summary

HoistScraper v0.1 delivers an end‑to‑end pipeline that lets non‑technical users:

1. **Bulk‑upload** a CSV of funding‑opportunity websites.
2. **Persist** those sites in a relational database for tracking.
3. **Trigger headless scrapes** (Playwright) that capture raw HTML/JSON.
4. **Store results** under `/data/{job_id}.json` and surface basic job status.
5. **View** sites, jobs, and raw results in a minimal dashboard.

The release is intentionally minimal—but production‑ready—so we can iterate on selectors and UI polish later.

---

## 1. Scope

| **In‑Scope**                                          | **Out‑of‑Scope (v0.1)**                 |
| ----------------------------------------------------- | --------------------------------------- |
| SQLModel schema (`Website`, `ScrapeJob`)              | Granular content selectors / extraction |
| CSV ingest (upload + CLI + auto‑seed)                 | Authentication / multi‑tenant access    |
| Redis + RQ job queue, Playwright worker               | Full‑featured admin UI                  |
| Basic Next.js dashboard (Sites, Jobs, Results)        | OAuth, RBAC, audit logs                 |
| CI pipeline (ruff, mypy, pytest, tsc, Playwright e2e) | Advanced analytics / reporting          |
| Render deploy: API, static FE, worker                 | PDF/‐‑to‑text extraction                |

---

## 2. Success Metrics

* **Time‑to‑green‑deploy** on a fresh Render stack ≤ 15 min.
* **CI pipeline** completes < 4 min on PR.
* **Scrape health**: triggering a scrape on any seeded site produces a non‑empty JSON file.
* **Test coverage** ≥ 90 % for Python units, 1 happy‑path Playwright e2e.

---

## 3. Engineering Principles

1. **Plan → Slice → Code.** Each slice has its own miniature PRD.
2. **Isolation First.** Every slice lives in a dedicated `git worktree` and (if necessary) a custom Docker image.
3. **Test‑Driven.** Write/extend tests before implementation; CI must stay ��.
4. **Robust CI/CD.** GitHub Actions pipeline gates merges on lint, type‑check, unit, e2e.
5. **PR Ritual.** PRs reviewed by **CodeRabbit**; **Claude‑Merge** agent merges on "#merge" when CI is green.
6. **Fix Fast.** Any red build produces an immediate surgical PR with failing test first.

---

## 4. Delivery Blocks

Each block is a *surgical task* with its own worktree, branch, tests, CI job and PR checklist.

### �� Block A — `bootstrap-db`

| Field              | Value                                                             |
| ------------------ | ----------------------------------------------------------------- |
| **Goal**           | Persist `Website` + `ScrapeJob`; CRUD `/api/sites`.               |
| **Functional**     | \* POST `/api/sites` (idempotent by URL).<br>\* GET `/api/sites`. |
| **Non‑Functional** | Duplicate URL ⇒ HTTP 409.<br>Unit‑test coverage ≥ 90 %.           |
| **CI Job**         | `test-db` – spins Postgres, runs `tests/test_db.py`.              |
| **PR Checklist**   | Tables auto‑create, duplicate guard, CI green, CodeRabbit ✅.      |

### �� Block B — `csv-ingest`

| Field            | Value                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Goal**         | Upload + CLI import of CSV, auto‑seed via `CSV_SEED_PATH`.                                                                      |
| **Functional**   | \* `/api/ingest/csv` dedup‑inserts.<br>\* CLI `python -m hoistscraper.cli.import_csv`.<br>\* Auto‑seed once on container start. |
| **Performance**  | Import 10 k rows in < 30 s, O( memory ≤ 500 MB ).                                                                               |
| **CI Job**       | `test-ingest` – depends `test-db`, runs ingest & seed tests.                                                                    |
| **PR Checklist** | Dedup safe, large CSV memory‑safe, seed logs once, CI green.                                                                    |

### �� Block C — `queue-worker`

| Field            | Value                                                                      |
| ---------------- | -------------------------------------------------------------------------- |
| **Goal**         | Redis + RQ queue, Playwright worker, `/api/scrape/{site_id}`.              |
| **Functional**   | \* Enqueue job, persist status.<br>\* Worker writes `/data/{job_id}.json`. |
| **CI Job**       | `test-queue` – uses `fakeredis`, unit‑tests worker transitions.            |
| **PR Checklist** | Job state machine correct, JSON file exists, CI green.                     |

### �� Block D — `dashboard-mvp`

| Field          | Value                                                                                             |
| -------------- | ------------------------------------------------------------------------------------------------- |
| **Goal**       | Next.js dashboard (Sites, Jobs, Results).                                                         |
| **Functional** | \* Upload CSV, list sites, run scrape, view JSON.<br>\* React‑Query hooks with shared `apiFetch`. |
| **CI Job**     | `test-fe` – vitest unit + Playwright e2e happy path.                                              |

### �� Block E — `ci-hardening`

Hard‑gate pipeline: ruff, mypy --strict, tsc, e2e.

### �� Block F — `render-stack`

Render blueprint (API, static FE, worker), health checks, Sentry.

---

## 5. CI/CD Overview

* **Jobs** chain: `test-db` → `test-ingest` → `test-queue` → `test-fe` → `lint‑and‑typecheck`.
* **Required checks for merge:** all �� plus CodeRabbit review.

---

## 6. Merge & Release Process

1. Developer pushes feature branch.
2. CI runs; CodeRabbit reviews.
3. Developer comments **`#merge`**.
4. **Claude‑Merge** agent:
   * Squash merges → `main`.
   * Deletes branch & worktree.
5. Render auto‑deploys **main**; smoke tests run.

---

## 7. Open Questions / Risks

* Selector configuration currently placeholder (`selectors={}`); will require follow‑up in v0.2.
* Playwright in slim image may need additional fonts/Chrome deps—monitor first worker deploy.
* Large CSV (> 50k rows) path needs memory profiling.

---

## 8. Infrastructure & Deployment

### Render Services

| Service              | Plan               | Description                                                                                                                                                            |
| -------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **hoistscraper**     | *Web Service*      | FastAPI backend at `/api/*`, serves static Next.js build at `/`, health check `/health`.                                                                              |
| **daily‑crawl**     | *Background Worker* | Pops from Redis queue, runs Playwright scrapes, writes `/data/{job_id}.json`.                                                                                         |
| **hoistscraper‑fe** | *Static Site*       | Next.js build output, CDN‑cached, fallback to backend for `/api/*` path.                                                                                             |
| **hoistscraper‑db** | *PostgreSQL 16*     | Relational store for `Website` and `ScrapeJob` tables, managed backups & monitoring handled by Render.                                                               |

### Networking / Data‑flow

1. **User** hits **hoistscraper‑fe** → browser fetches `/api/sites` from **hoistscraper**.
2. CSV upload posts to `/api/ingest/csv` → rows persisted in **hoistscraper‑db**.
3. Clicking *Run Scrape* calls `/api/scrape/{site_id}` → job enqueued in Redis.
4. **daily‑crawl** worker pops job, runs Playwright ➜ writes `{job_id}.json` under `/data`.
5. Frontend polls `/api/jobs` & fetches `/data/{job_id}.json` to display raw output.

> **Scaling notes**  
> *API & Worker images share a base layer with Playwright; scale horizontally by increasing plan size or replica count.*

### Future Containers (not yet provisioned)

* **redis** (add‑on) – to be attached once queue block is merged.
* **sentry-relay** (optional) – centralised logging & error capture.

---

## 🛡️ Implementation Guard‑Rails

The points below tighten the spec so autonomous agents (Claude Code, CodeRabbit, CI) can work **deterministically** and avoid common prod surprises.

### 8.1 Environment Variable Contract

| Key                        | Default (local)                                         | Consumed by         | Notes                                |
| -------------------------- | ------------------------------------------------------- | ------------------- | ------------------------------------ |
| `DATABASE_URL`             | `postgresql://postgres:postgres@localhost/hoistscraper` | API + Worker        | Auto‑injected by Render DB service  |
| `REDIS_URL`                | `redis://localhost:6379`                               | API + Worker        | Auto‑injected by Render Redis addon |
| `CSV_SEED_PATH`            | `./backend/sites.yml`                                  | API (startup)       | Auto‑seed on container start        |
| `MAX_WORKERS`              | `2`                                                     | Worker              | Concurrent Playwright sessions       |
| `PLAYWRIGHT_TIMEOUT_MS`    | `30000`                                                 | Worker              | Per‑page scrape timeout             |
| `SENTRY_DSN`               | *(unset)*                                               | API + Worker + FE   | Error tracking (optional)            |
| `ALLOWED_ORIGINS`          | `*` (dev), space‑separated (prod)                      | API CORS            | Security boundary                    |
| `NEXT_PUBLIC_API_URL`      | `http://localhost:8000`                                 | Frontend            | API base URL for client‑side calls   |

### 8.2 Health Check Endpoints

| Service              | Port      | Path      | Expected Response                     |
| -------------------- | --------- | --------- | ------------------------------------- |
| API                  | `8000`    | `/health` | `{"status": "healthy"}`               |
| Frontend (static)    | CDN / 443 | *n/a*     |                                       |
| Worker               | *none*    | Lifecycle checked via container liveness. |
| Cron (`daily-crawl`) | *none*    | Render cron logs success/fail.            |
| Ollama               | `11434`   | `/`       | 200.                                  |

### 8.3 Playwright Dependencies

* Worker Dockerfile must run `playwright install --with-deps chromium` which installs `libnss3`, `libatk1.0-1`, `libxcb1`, fonts, etc. If Alpine is preferred, pin `--with-deps=alpine`. Add `--no-sandbox` arg when launching headless in Render.

### 8.4 Schema Migration Strategy

* v0.1: rely on `SQLModel.metadata.create_all` (drop‑and‑recreate allowed in dev).
* v0.2+: introduce Alembic + autogenerate migrations; PRD calls this out for future sprints.

### 8.5 Testing Fixtures

* Commit `tests/fixtures/mini_sites.csv` (5 rows) and `tests/fixtures/dummy_page.html` (for scraper unit tests).

### 8.6 Error‑Handling Contract

* JSON shape: `{ "code": int, "message": str, "details"?: Any }`.
* 409 → duplicate URL, 422 → validation, 500 → unhandled.

### 8.7 Concurrency & Resource Budgets

* `MAX_WORKERS` env caps simultaneous Playwright sessions (default 2). Each Chromium ≈ 125 MB RAM; keep total below 512 MB Render Starter limit.

### 8.8 Logging & Tracing

* Use `loguru` in python services → JSON logs to stdout.
* Structured fields: `service`, `level`, `timestamp`, `msg`, `job_id?`.
* Sentry integration toggled by `SENTRY_DSN` env.

### 8.9 CORS & Auth

* Dev: `allow_origins=['*']`. Prod: split‑space `ALLOWED_ORIGINS` env.
* Auth TBD (v0.2) – JWT or cookie‑based sessions.

### 8.10 Merge‑Bot Commands

* `#merge` – squash‑merge when CI + CodeRabbit green.
* `#retest` – re‑kick CI.
* `#deploy-preview` – creates temporary Render preview stack.

### 8.11 Staging vs. Production

* Render **Preview Environment Group** spins up per‑PR: all services use **Starter‑preview** plan, DB = Ephemeral Postgres.
* Automatic destroy on PR close.

### 8.12 Test‑Safe Scraper Target

* Use `https://httpbin.org/html` in CI e2e tests – deterministic HTML; avoids hitting real grant sites under load.

---