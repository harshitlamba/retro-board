# Architecture — Weekly Feedback & Retrospective Tool

Companion to [`plan.md`](./plan.md). `plan.md` defines _what_ the MVP does; this
document defines _how_ it is built. Section references like "plan §6" point back
to `plan.md`.

---

## 1. Overview

A responsive server-rendered Django web application for **one team managing
multiple projects**. Members continuously submit structured, identified or
anonymous feedback. Claude aggregates that feedback into proposed themes. A single
facilitator curates and prioritises themes through weighted voting, then runs a
weekly retrospective that produces decisions and trackable actions.

The system is a single Django project. Long-running and scheduled work (the AI
call, notification sweeps) runs out-of-process via a lightweight task queue
(django-q2), which uses the application database as its broker — no extra
infrastructure service. There is no separate frontend build beyond a CSS
pipeline; interactivity is delivered with HTMX and Alpine.js against
Django-rendered HTML partials.

---

## 2. Technology stack

| Layer                 | Choice                                                                     | Rationale                                                                                                                                                                                                                                                                               |
| --------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Language              | Python 3.14                                                                | Latest stable release.                                                                                                                                                                                                                                                                  |
| Web framework         | Django 6.1                                                                 | Batteries included: ORM, migrations, auth, admin, forms. Its permissions model and admin collapse the three heaviest parts of the spec (RBAC, facilitator curation UI, scheduled work). (Django 5.2 is the current LTS — a valid conservative substitute; 5.1 is end-of-life.)          |
| Database              | PostgreSQL 18                                                              | Relational integrity for the many-to-many links (feedback↔themes, member↔projects), `JSONB` for AI theme payloads, `GROUP BY` covers all MVP analytics. Also the task-queue broker (see below).                                                                                         |
| Templating / UI       | Django templates + HTMX 2 + Alpine.js                                      | Single codebase, minimal JavaScript. HTMX handles partial re-renders (live vote tallies, inline theme editing, the retro board); Alpine handles small local UI state. (Stay on the HTMX 2 line — htmx 4 exists but is tagged `next`, not the default release, until 2027.)              |
| Styling               | Tailwind CSS v4 via `django-tailwind-cli`                                  | Utility-first, responsive by default (plan §18). The `-cli` package drives Tailwind's standalone binary — compiled to a static bundle, no Node toolchain at all.                                                                                                                        |
| Background jobs       | **django-q2**                                                              | Lightweight task queue. Uses the **application database as the broker** (`orm` mode — no Redis, no extra service) and ships a **built-in scheduler** for the notification sweeps. A single `qcluster` process runs workers + scheduler. Swappable for Celery later if scale demands it. |
| AI                    | `anthropic` Python SDK, model `claude-sonnet-5`                            | Fast and inexpensive ($2 / $10 per MTok); more than capable of grouping short feedback into themes. Haiku 4.5 is a drop-in cost step-down; Opus 5 only if quality proves insufficient. Uses **structured outputs** (JSON schema) so themes come back validated.                         |
| Authentication        | Django built-in auth + custom `User` model (email as the login identifier) | plan §2: simple email/password. No SSO, no allauth. Session cookies, CSRF protection on.                                                                                                                                                                                                |
| Facilitator tooling   | Customised Django admin (`ModelAdmin` + admin actions)                     | plan §7 / §10. Theme edit/merge/split/delete, feedback association, de-anonymisation, and action tracking are built as tailored admin screens for the single facilitator.                                                                                                               |
| Configuration         | `django-environ`, split settings                                           | `settings/base.py`, `settings/dev.py`, `settings/prod.py`. All secrets via environment variables.                                                                                                                                                                                       |
| Testing               | `pytest-django` + `factory_boy` + `coverage`                               | Privacy rules (plan §5) get dedicated test coverage.                                                                                                                                                                                                                                    |
| Dependency management | `uv`                                                                       | Fast, lockfile-based (`uv.lock`), single tool for venv + installs.                                                                                                                                                                                                                      |
| Containerisation      | Docker + Docker Compose                                                    | Services: `web`, `qcluster`, `db`. Static files via WhiteNoise.                                                                                                                                                                                                                         |

### 2.1 Version pins (verified 2026-09-03)

Latest stable at the time of writing. Treat as floors; `uv.lock` is the source of
truth once the project is scaffolded.

| Component             | Version              |
| --------------------- | -------------------- |
| Python                | 3.14.x               |
| Django                | 6.1.x (or 5.2.x LTS) |
| PostgreSQL            | 18.x                 |
| HTMX                  | 2.0.x                |
| Alpine.js             | 3.16.x               |
| Tailwind CSS          | 4.3.x                |
| `django-tailwind-cli` | 4.6.x                |
| `django-q2`           | 1.9.x                |
| `anthropic` (SDK)     | ≥ 0.120              |
| `django-environ`      | 0.14.x               |
| `pytest-django`       | 4.14.x               |
| `factory_boy`         | 3.3.x                |
| `coverage`            | 7.x                  |
| `gunicorn`            | 26.x                 |
| `whitenoise`          | 6.12.x               |
| `uv`                  | 0.12.x               |
| `ruff`                | 0.16.x               |

Claude model: `claude-sonnet-5` (current latest Sonnet; released 2026-06-30).

---

## 3. Runtime topology

```text
                    ┌─────────────────────────────┐
   Browser ───────► │  web  (Django + Gunicorn)    │
   (HTMX)  ◄─────── │  - request/response          │
                    │  - Django admin (facilitator)│
                    └──────────────┬──────────────┘
                                   │ read/write
                                   │ + enqueue task (INSERT)
                                   ▼
                       ┌────────────────────────┐
                       │ db (PostgreSQL)        │
                       │ - application data     │
                       │ - django-q2 task queue │
                       └───────────┬────────────┘
                                   ▲ poll / claim / write result
                                   │
              ┌────────────────────┴────────────────────┐
              │ qcluster (django-q2)                     │
              │ - workers:   generate_themes ───────────┼──► Claude API
              │ - scheduler: notification sweeps        │
              └─────────────────────────────────────────┘
```

- **`web`** — synchronous request handling only. Never calls the Claude API
  directly; it enqueues a task (a row in the queue table) and returns
  immediately.
- **`qcluster`** — a single django-q2 process running both the task workers
  (`generate_themes`, notification fan-out) and the scheduler (upcoming-retro
  reminder, action due/overdue sweep).
- **`db`** — single source of truth _and_ the task-queue broker; no separate
  broker service.

---

## 4. Django project layout

```text
project-with-feedback/
├── _docs/
│   ├── plan.md
│   └── architecture.md
├── config/                     # project package
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── accounts/               # custom User, roles, auth views
│   ├── teams/                  # Team (singleton), Project, Membership
│   ├── feedback/               # Feedback submissions + visibility managers
│   ├── themes/                 # Theme, ThemeFeedback, Vote, AI generation
│   ├── retro/                  # Retrospective, DiscussionNote, Decision, Action
│   ├── notifications/          # Notification model + scheduled task functions
│   └── analytics/              # read-only aggregation views
├── templates/                  # project-level templates + partials
├── static/
├── tests/                      # cross-app tests (privacy matrix, workflows)
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

Each app under `apps/` owns its models, views, urls, forms, `admin.py`, and
`tasks.py` (django-q2 task functions) where relevant.

---

## 5. Application modules

### 5.1 `accounts` (plan §2)

- **`User`** — custom model, `AbstractBaseUser` + `PermissionsMixin`. Login
  identifier is `email`. Fields: `name`, `email`, `password`, `is_facilitator`
  (mirrors the team facilitator FK for quick checks), plus standard flags.
- **`Role`** — enum/choice field on `Membership` (e.g. `contributor`,
  `project_owner`). The facilitator is designated on `Team`, not via role.
- Views: sign up, log in, log out, minimal profile. Session-based.

### 5.2 `teams` (plan §1, §10)

- **`Team`** — effectively a singleton for the MVP. Holds `facilitator`
  (FK → `User`).
- **`Project`** — belongs to the team; `is_active` flag.
- **`Membership`** — `User` ↔ `Project` (many-to-many through model) with `role`.
  A user can belong to multiple projects.

### 5.3 `feedback` (plan §3, §4, §5)

- **`Feedback`**
  - Reflection: `what_worked`, `what_didnt_work` (text).
  - Start–Stop–Continue: `start`, `stop`, `continue_` (text).
  - Target: exactly one of `team` / `project` / `subject_user` (validated in
    `clean()`).
  - `author` (FK → `User`, **always set**), `is_anonymous` (bool),
    `created_at`.
- **Visibility** is enforced in one place: `FeedbackQuerySet.visible_to(user)`.
  - Contributor: only rows where `author == user`.
  - Facilitator: all rows for the team and its projects, **including the author
    of anonymous feedback**.
  - No peer browsing of raw feedback.
- Views: submit feedback, "my submissions" history. No list view exposes other
  users' rows.

### 5.4 `themes` (plan §6, §7, §8)

- **`Theme`** — `title`, `description`, `retrospective` (FK), `origin`
  (`ai` | `facilitator`), `ai_payload` (`JSONB`, nullable), `discussion_eligible`
  (bool, derived from vote total).
- **`ThemeFeedback`** — through model linking `Theme` ↔ `Feedback` (supporting
  evidence). Facilitator can associate/dissociate.
- **`Vote`** — `member` (FK → `User`), `theme` (FK), `count` (1–3),
  `retrospective` (FK). Constraint: a member's summed `count` per retrospective
  ≤ 3. Votes are facilitator-visible only.
- **AI generation** — `themes/tasks.py::generate_themes(retrospective_id)`:
  1. Collect in-scope `Feedback` for the retrospective.
  2. Call `claude-sonnet-5` with a JSON-schema structured output:
     `{ "themes": [ { "title", "description", "feedback_ids": [int] } ] }`.
  3. Persist results as **proposed** `Theme` + `ThemeFeedback` rows
     (`origin="ai"`).
  4. Facilitator curates in the admin.
  - The instruction/prompt prefix is prompt-cached for re-runs.
  - The task is idempotent per run: it replaces prior _unedited_ AI proposals for
    that retrospective.
- **Curation** — Django admin actions: merge themes, split a theme, edit
  title/description, delete, create from scratch, attach/detach feedback
  (plan §7). AI never edits or deletes; it only proposes (plan §6 exclusions).

### 5.5 `retro` (plan §9, §11, §12, §13, §14)

- **`Retrospective`** — one per week for the team. `scheduled_for`, `status`
  (`planned` | `in_progress` | `closed`), `facilitator` snapshot.
- **`DiscussionNote`** — per discussed theme: `notes`, `key_observations`.
- **`Decision`** — `decision`, `context`, `date`, `owner` (optional). Separate
  from actions by design (plan §12).
- **`Action`** — `description`, `owner` (FK → `User`), `due_date`, `status`
  (`open` | `in_progress` | `done` | `cancelled`), `expected_outcome`
  (optional), `actual_outcome` (optional), `retrospective` (FK).
- **Follow-up** — creating a new `Retrospective` auto-attaches unresolved
  `Action`s from the previous one so they appear on the agenda
  (Previous action → Status → Outcome → Follow-up).

### 5.6 `notifications` (plan §15)

- **`Notification`** — `recipient`, `kind` (`retro_upcoming` |
  `action_assigned` | `action_due` | `action_overdue`), `payload`, `created_at`,
  `read_at`. Rendered in-app; no email/Slack in the MVP.
- **Scheduled tasks (django-q2 scheduler)**
  - `notify_upcoming_retro` — daily; fires when a retrospective is within the
    reminder window.
  - `sweep_actions_due` — daily; creates `action_due` / `action_overdue`
    notifications from `Action.due_date` vs. today.
  - `action_assigned` is enqueued inline when an action is created/reassigned.

### 5.7 `analytics` (plan §17)

Read-only. Aggregation queries over operational tables — no warehouse, no
separate pipeline:

- feedback submission counts (overall, per project, team vs. project),
- themes over time, recurring themes,
- vote distribution,
- open vs. completed actions.

Product/team metrics only — no employee-level scoring (plan §17 exclusions).

---

## 6. Data model (relationships)

```text
User ──< Membership >── Project ──> Team
  │                                  │
  │                                  └── facilitator ──> User
  │
  ├──< Feedback (author)            Feedback.target = Team | Project | User
  │        │
  │        └──< ThemeFeedback >── Theme ──> Retrospective
  │                                 │
  ├──< Vote >───────────────────────┘
  │
  ├──< Action (owner) ──> Retrospective
  ├──< Decision (owner, optional) ──> Retrospective
  └──< Notification (recipient)

Retrospective ──< DiscussionNote ──> Theme
```

---

## 7. Authentication & authorisation

- **Authentication** — Django session auth. Custom `User` with email login,
  password hashed with Django's default (PBKDF2). CSRF on for all mutating
  requests; `SECURE_*` settings enabled in `prod`.
- **Authorisation — two tiers:**
  1. _Contributor_ — authenticated member. Can submit feedback, see only their
     own submissions, cast votes, view themes/agenda for their team, own their
     actions.
  2. _Facilitator_ — the one `Team.facilitator`. Everything a contributor can do,
     plus: view all feedback (incl. anonymous authorship), curate themes, manage
     voting, run the retrospective, record decisions/actions, access the
     facilitator admin.
- **Enforcement points**
  - `Feedback` visibility → `FeedbackQuerySet.visible_to(user)`, used by every
    view and serializer path. No view queries `Feedback.objects.all()`.
  - Facilitator-only views → `FacilitatorRequiredMixin` / a `user_passes_test`
    decorator checking `request.user == team.facilitator`.
  - Django admin → restricted to the facilitator (and superuser for ops).
- **Privacy test matrix** (`tests/`) — for each role × each feedback
  visibility rule, assert allowed access succeeds and forbidden access returns
  403/404 and is absent from list/detail responses.

---

## 8. AI integration details

- **Trigger** — facilitator action ("Generate themes") on a retrospective →
  enqueues `generate_themes`. Never runs in the request/response cycle.
- **Model** — `claude-sonnet-5` via the official `anthropic` SDK.
- **Prompt shape**
  - Stable, prompt-cached prefix: role, task description, theme-quality
    guidance, output contract.
  - Volatile suffix: the retrospective's feedback items (id + structured
    fields).
- **Structured output** — JSON schema constrains the response to
  `{ "themes": [ { "title": str, "description": str, "feedback_ids": [int] } ] }`.
  Parsed with `json.loads`, validated against known feedback ids before write.
- **Persistence** — proposals written as `Theme(origin="ai")` +
  `ThemeFeedback`. Facilitator edits are marked so a re-run does not clobber
  them.
- **Boundaries** (plan §6 exclusions) — no scoring, no evaluation of people, no
  autonomous facilitation, no deciding what the team must do. Proposal only.
- **Failure handling** — task retries with backoff on transient API errors; a
  terminal failure records an error state visible to the facilitator, who can
  retry or curate manually.
- **Cost/perf** — feedback volume per retrospective is small; a single call per
  generation. Caching the prefix keeps re-runs cheap.

---

## 9. Background processing

| Task                                | Type      | Cadence / trigger           | Owner app       |
| ----------------------------------- | --------- | --------------------------- | --------------- |
| `generate_themes(retrospective_id)` | on-demand | facilitator action          | `themes`        |
| `notify_upcoming_retro`             | scheduled | daily (django-q2 scheduler) | `notifications` |
| `sweep_actions_due`                 | scheduled | daily (django-q2 scheduler) | `notifications` |
| `emit_action_assigned(action_id)`   | on-demand | action create/reassign      | `notifications` |

- Broker + result backend: the application PostgreSQL database (django-q2 `orm`
  mode). No separate broker service.
- Tasks are idempotent; scheduled sweeps guard against duplicate notifications
  with a uniqueness check on `(recipient, kind, target, date)`.
- Retry/backoff on transient failures is configured via `Q_CLUSTER`
  (`retry`, `max_attempts`, `timeout`).

---

## 10. Configuration & secrets

- `django-environ` reads a `.env` in development; real environment variables in
  production.
- Required variables: `DJANGO_SECRET_KEY`, `DATABASE_URL`,
  `ANTHROPIC_API_KEY`, `DJANGO_SETTINGS_MODULE`, `ALLOWED_HOSTS`,
  `DJANGO_DEBUG`. (No `REDIS_URL` — the task queue uses `DATABASE_URL`.)
- `settings/base.py` holds shared config; `dev.py` enables debug tooling;
  `prod.py` enables `SECURE_SSL_REDIRECT`, HSTS, secure cookies, and WhiteNoise.

---

## 11. Testing strategy

- **Framework** — `pytest-django`, `factory_boy` factories per model,
  `coverage`.
- **Priorities**
  1. Privacy matrix (plan §5) — the highest-risk surface.
  2. Vote constraints — ≤ 3 per member per retrospective, splitting, the
     ≥ 3 eligibility threshold.
  3. Retro follow-up — unresolved actions carry into the next retrospective.
  4. `generate_themes` — Claude client mocked; assert parsing, id validation,
     idempotent re-run, and that facilitator edits survive.
  5. Notification sweeps — due/overdue boundary dates, no duplicates.
- **CI** — run `pytest` + `ruff` on push.

---

## 12. Deployment

Docker Compose is the deployment unit. No cloud-provider-specific setup.

- **Image** — single Dockerfile; the same image runs `web` and `qcluster` with
  different commands.
- **Compose services**
  - `web` — Django under Gunicorn.
  - `qcluster` — `python manage.py qcluster` (django-q2 workers + scheduler).
  - `db` — PostgreSQL 18, with a named volume for persistence.
- **Static files** — collected at build time, served by WhiteNoise.
- **Migrations** — run as a release step before `web` starts.
- **Environment** — supplied via an `.env` file / Compose `environment:` block
  (see §10).

---

## 13. Explicit non-goals (from `plan.md`)

Multiple teams / orgs / departments; SSO / SCIM; audio-video or file-attachment
feedback; numeric ratings or performance scores; public or peer-browsable
feedback feeds; ranked-choice or configurable voting; daily or per-project
retrospective engines; meeting transcription; external integrations (Jira,
GitHub, Linear, Slack, Teams, Google Workspace); native mobile apps;
employee-level analytics of any kind.
