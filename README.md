# retro-board

A web application for **one team managing multiple projects** that lets members
continuously submit structured, identified or anonymous feedback; uses AI to
aggregate that feedback into themes; lets a facilitator curate and prioritise
those themes through three-vote weighted voting; and turns the highest-priority
themes into facilitated retrospective discussions, decisions, and trackable
actions.

## Status

Planning / pre-implementation. No application code yet — see the backlog.

## Documentation

| Document | Purpose |
|---|---|
| [`_docs/plan.md`](_docs/plan.md) | Product scope, MVP decisions, and core workflow |
| [`_docs/architecture.md`](_docs/architecture.md) | Tech stack, version pins, project layout, data model, testing, deployment |
| [`_docs/tasks.md`](_docs/tasks.md) | Session-sized, independently workable backlog |

## Tech stack (summary)

Django 6.1 · PostgreSQL 18 · Django templates + HTMX 2 + Alpine.js ·
Tailwind CSS v4 (`django-tailwind-cli`) · `django-q2` background jobs ·
`anthropic` SDK (`claude-sonnet-5`) for theme generation · `uv` · Docker Compose.

See [`_docs/architecture.md`](_docs/architecture.md) for the full stack and
pinned versions.
