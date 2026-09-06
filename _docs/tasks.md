# Backlog — Weekly Feedback & Retrospective Tool

Shared context for every task: read [`plan.md`](./plan.md) (what the MVP does)
and [`architecture.md`](./architecture.md) (how it is built — stack, version
pins, app layout, data model). Each task below is scoped to one working session
and written to stand alone: it names the app it touches, what to build, and what
"done" looks like. Where a task needs another to exist first, that prerequisite
is stated in its description rather than assumed.

Definition of done for every task: new code has tests, `pytest` passes, `ruff`
is clean, and any model change ships with its migration.

---

## 1. Project scaffold with a passing test
Goal: An empty but runnable Django project with one green test.
Description: Create the Django project package `config/` with a single app-less
setup, managed by `uv` (`pyproject.toml`, `uv.lock`) using the versions in
architecture.md §2.1. Wire up `pytest` + `pytest-django`, add one trivial test
that asserts the Django settings import and `1 + 1 == 2`, and confirm
`uv run pytest` exits zero. No database, Docker, or apps yet.

## 2. Settings split and environment configuration
Goal: `base` / `dev` / `prod` settings modules reading from the environment.
Description: Split settings into `config/settings/{base,dev,prod}.py` and load all
secrets and environment-specific values via `django-environ` (`DJANGO_SECRET_KEY`,
`DATABASE_URL`, `ANTHROPIC_API_KEY`, `ALLOWED_HOSTS`, `DJANGO_DEBUG`). Point the
database at PostgreSQL 18 via `DATABASE_URL`, add a committed `.env.example`, and
have `prod.py` enable the secure-cookie / HSTS / SSL-redirect settings. Assumes
the scaffold from task 1 exists.

## 3. Docker Compose for local development
Goal: `docker compose up` starts the app against Postgres.
Description: Write a single `Dockerfile` and a `docker-compose.yml` with three
services — `web` (Django under Gunicorn), `qcluster` (placeholder command for
now), and `db` (PostgreSQL 18 with a named volume). Run migrations as a start
step, serve static files with WhiteNoise, and document the one-command startup.
Assumes environment-based settings (task 2) are in place.

## 4. Base templates, Tailwind, and HTMX/Alpine wiring
Goal: A styled base layout that loads HTMX and Alpine.
Description: Add `django-tailwind-cli` (Tailwind v4, standalone binary — no Node),
create `templates/base.html` with a header/nav/content structure, and include
HTMX 2 and Alpine.js 3.16 as static assets. Add an authenticated placeholder
home view at `/` that extends the base template. Assumes the project scaffold
(task 1) exists.

## 5. django-q2 task queue integration
Goal: Background tasks run via a `qcluster` process using the database broker.
Description: Add `django-q2` to installed apps, configure `Q_CLUSTER` in
`orm` mode (no Redis) with retry/timeout defaults, and run its migrations. Add a
throwaway `ping` task plus a test that enqueues it synchronously and asserts the
result, and update the Compose `qcluster` service to run `manage.py qcluster`.
Assumes environment-based settings (task 2) exist.

## 6. Custom User model
Goal: An email-login `User` model in a new `accounts` app.
Description: Create `apps/accounts` with a `User` model based on
`AbstractBaseUser` + `PermissionsMixin`, using `email` as `USERNAME_FIELD`, plus
`name` and an `is_facilitator` flag; add its manager and admin registration.
Set `AUTH_USER_MODEL` before the first migration and generate that migration.
This must land early — changing the user model later is disruptive.

## 7. Signup, login, and logout
Goal: A member can create an account and sign in.
Description: Add signup, login, and logout views and templates in `apps/accounts`
using Django's session auth and the custom `User` model, with email + password
fields and Django's password validators. Redirect authenticated users to the
home page and cover the happy path and bad-credentials path with tests. Assumes
the custom `User` model (task 6) exists.

## 8. Role-based access-control helpers
Goal: Reusable guards for "logged-in" and "facilitator-only" views.
Description: Add a `FacilitatorRequiredMixin` (and matching decorator) that
checks `request.user` is the team's facilitator, plus a project-wide default that
every view requires login unless explicitly public. Unit-test all three outcomes
(anonymous, contributor, facilitator) against dummy views. Assumes the custom
`User` model (task 6) exists; the facilitator is identified by `User.is_facilitator`
until the `Team` model (task 9) lands.

## 9. Teams, projects, and memberships
Goal: Models for the one team, its projects, and who belongs to what.
Description: Create `apps/teams` with `Team` (treated as a singleton, holds a
`facilitator` FK to `User`), `Project` (belongs to the team, `is_active` flag),
and `Membership` (a `User`↔`Project` through model with a `role` choice). Register
all three in the admin and generate migrations. See architecture.md §5.2 and
plan §1 / §10.

## 10. Feedback submission model
Goal: The `Feedback` model that stores one structured submission.
Description: Create `apps/feedback` with a `Feedback` model holding the reflection
fields (`what_worked`, `what_didnt_work`), the start/stop/continue fields, a
target that is exactly one of team / project / subject-user (enforced in
`clean()`), plus `author` (always set), `is_anonymous`, and `created_at`.
Register it in the admin and generate the migration. See architecture.md §5.3
and plan §3.

## 11. Feedback visibility rules and privacy tests
Goal: A single queryset method that enforces who can see which feedback.
Description: Add `FeedbackQuerySet.visible_to(user)` so a contributor sees only
their own rows and the facilitator sees all team/project rows including the
author of anonymous submissions, with no peer browsing. Write the privacy test
matrix: for each role × each rule, assert allowed access succeeds and forbidden
access is absent. Assumes the `Feedback` model (task 10) and access helpers
(task 8) exist; see plan §5.

## 12. Feedback submission form and view
Goal: A logged-in member can submit feedback through the UI.
Description: Build a Django form and view for creating `Feedback`, rendered in a
template that extends the base layout, with the identified/anonymous toggle and
target selection. Submit and validate via HTMX, showing inline field errors and
a success partial. Assumes the `Feedback` model (task 10) and base templates
(task 4) exist.

## 13. "My feedback" history view
Goal: A member can review everything they have submitted.
Description: Add a list view and template showing the current user's own
submissions newest-first, using `Feedback.objects.visible_to(request.user)` so
the privacy rules are honoured. Include empty-state handling and a link to each
submission's detail. Assumes feedback visibility (task 11) exists; see plan §4.

## 14. Theme, ThemeFeedback, and Vote models
Goal: Models for aggregated themes, their supporting feedback, and votes.
Description: Create `apps/themes` with `Theme` (`title`, `description`,
`retrospective` FK, `origin` = ai|facilitator, nullable `ai_payload` JSON,
`discussion_eligible` flag), `ThemeFeedback` (a `Theme`↔`Feedback` through
model), and `Vote` (`member`, `theme`, `count` 1–3, `retrospective`). Add a
constraint that a member's summed votes per retrospective cannot exceed 3, and
generate migrations. See architecture.md §5.4 and plan §6 / §8.

## 15. Anthropic client wrapper
Goal: One tested, mockable function that turns feedback into proposed themes.
Description: Add a module in `apps/themes` that calls `claude-sonnet-5` via the
`anthropic` SDK with a JSON-schema structured output of
`{themes: [{title, description, feedback_ids: [int]}]}`, using a stable
prompt-cached instruction prefix and a volatile feedback suffix. Return parsed,
schema-validated data and raise a typed error on failure. Test it with the SDK
client mocked — no live API calls. See architecture.md §8.

## 16. generate_themes background task
Goal: A django-q2 task that produces proposed themes for a retrospective.
Description: Implement `generate_themes(retrospective_id)` that collects the
retrospective's in-scope feedback, calls the Anthropic wrapper, and persists the
result as `Theme(origin="ai")` + `ThemeFeedback` rows, validating returned
feedback IDs. Make it idempotent: a re-run replaces prior *unedited* AI proposals
but leaves facilitator-edited themes alone. Assumes the theme models (task 14)
and Anthropic wrapper (task 15) exist.

## 17. Theme curation in the Django admin
Goal: The facilitator can fully control themes from the admin.
Description: Build tailored `ModelAdmin` screens for `Theme` supporting create,
edit, delete, and attach/detach of supporting `Feedback`, plus admin actions to
merge selected themes and to split a theme. Add an admin action on
`Retrospective` (or `Theme`) that enqueues `generate_themes` and surfaces its
status. Assumes the theme models (task 14) and the `generate_themes` task
(task 16) exist; see plan §7.

## 18. Retrospective, decision, and action models
Goal: Models for the weekly retrospective and its outputs.
Description: Create `apps/retro` with `Retrospective` (weekly, `scheduled_for`,
`status`), `DiscussionNote` (`notes`, `key_observations`, per discussed theme),
`Decision` (`decision`, `context`, `date`, optional `owner`), and `Action`
(`description`, `owner`, `due_date`, `status`, optional expected/actual
outcome). Register all in the admin and generate migrations. See
architecture.md §5.5 and plan §9 / §11 / §12 / §13.

## 19. Theme voting
Goal: Each member casts up to three votes per retrospective across themes.
Description: Build a voting view and template where a member allocates 3 votes
per retrospective, all on one theme or split across several, with live tallies
updated via HTMX. Enforce the per-member cap at the form and database level and
test the boundary (exactly 3, over 3, splitting, re-voting). Assumes the `Vote`
model (task 14) exists; see plan §8.

## 20. Discussion eligibility and vote visibility
Goal: Themes crossing the vote threshold are flagged; votes are facilitator-only.
Description: Derive `Theme.discussion_eligible` from a summed vote count of 3 or
more (eligibility only — it does not force discussion) and recompute it when
votes change. Ensure vote counts and voter identities are visible to the
facilitator and hidden from contributors. Assumes voting (task 19) exists; see
plan §8.

## 21. Retrospective agenda view
Goal: The facilitator sees a prioritised agenda for a retrospective.
Description: Build a facilitator-only view listing the retrospective's themes
ordered by vote count, each showing its tally, `discussion_eligible` state, and a
drill-down to supporting feedback and team/project context. Read feedback through
the visibility layer so anonymity is respected in the drill-down. Assumes
discussion eligibility (task 20) and the access helpers (task 8) exist; see
plan §9.

## 22. Discussion capture forms
Goal: The facilitator records notes, decisions, and actions during a retro.
Description: Add forms and views within a retrospective for creating
`DiscussionNote` entries per theme and for adding `Decision` and `Action`
records, each rendered in the retro template. Keep decisions and actions as
separate records per plan §12. Assumes the retro models (task 18) and the agenda
view (task 21) exist.

## 23. Action follow-up carry-over
Goal: Unresolved actions appear automatically in the next retrospective.
Description: When a new `Retrospective` is created, attach every `Action` from
the previous retrospective whose status is not done/cancelled so it shows on the
new agenda with its status and outcome. Cover the carry-over and the
"nothing outstanding" case with tests. Assumes the retro models (task 18) exist;
see plan §14.

## 24. Notifications model and in-app display
Goal: Users see their notifications inside the app.
Description: Create `apps/notifications` with a `Notification` model
(`recipient`, `kind`, `payload`, `created_at`, `read_at`), an admin registration,
and a template partial (e.g. a nav dropdown or list page) showing unread items
with a mark-as-read action. No email or Slack. See architecture.md §5.6 and
plan §15.

## 25. Notification-generating tasks
Goal: The three MVP notification triggers fire reliably and without duplicates.
Description: Implement `notify_upcoming_retro` and `sweep_actions_due` as
daily django-q2 scheduled tasks, and `emit_action_assigned` as an inline task
run when an action is created or reassigned. Guard against duplicates with a
uniqueness check on `(recipient, kind, target, date)` and test the due/overdue
boundary dates. Assumes the `Notification` model (task 24) and the retro models
(task 18) exist.

## 26. Analytics dashboard
Goal: A facilitator dashboard of product/team metrics.
Description: Create `apps/analytics` with read-only aggregation queries over the
operational tables — feedback submission counts (overall, per project, team vs.
project), themes over time, recurring themes, vote distribution, open vs.
completed actions — and a facilitator-only template rendering them. No
employee-level metrics. See architecture.md §5.7 and plan §17.

## 27. Seed data management command
Goal: One command populates a realistic demo dataset.
Description: Add a `manage.py seed_demo` command that creates the single team, a
handful of projects, several members (one facilitator), and a spread of sample
feedback across teams, projects, and individuals, identified and anonymous. Make
it idempotent or clearly destructive-then-recreate. Useful for manual testing and
demos of any other task.

## 28. CI workflow and developer setup docs
Goal: Every push runs the test suite and linter; setup is documented.
Description: Add a GitHub Actions workflow that installs dependencies with `uv`,
spins up PostgreSQL, and runs `pytest` and `ruff check`. Add a README section
covering local setup (`uv sync`, `.env` from `.env.example`, `docker compose up`,
running tests). Assumes the scaffold (task 1) and Compose setup (task 3) exist.
