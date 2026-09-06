from pathlib import Path

content = """# Weekly Feedback & Retrospective Tool — Final MVP Scope

## 1. Product structure

### Decision

One team, multiple projects.

### Why

This gives enough real-world complexity to test whether feedback can be meaningfully separated into team-level vs. project-level issues, while avoiding the complexity of supporting multiple teams and organizations.

### MVP

- 1 team
- Multiple active projects
- Users can belong to multiple projects
- Feedback can target either the team, a project, or an individual within that context

### Excluded

- Multiple teams
- Departments
- Organizations
- Cross-team projects

---

## 2. Authentication

### Decision

Simple email/password login.

### Why

Privacy requires authentication, but SSO provides no value for validating the core feedback workflow.

### MVP

- Sign up/login
- Name
- Email
- Password
- Role
- Team/project membership

### Excluded

- Google/Microsoft SSO
- SCIM
- Enterprise identity management

---

## 3. Feedback

### Decision

A structured feedback form.

Each submission contains:

### Reflection

- What worked?
- What didn't work?

### Start–Stop–Continue

- Start
- Stop
- Continue

### Metadata

- Team or project
- Optional individual being given feedback
- Identified/anonymous toggle
- Timestamp

### Why

A structured form gives consistent data that can subsequently be aggregated by AI. A completely free-form journal would make theme extraction and comparison much harder.

### Excluded

- Audio/video feedback
- File attachments
- Complex feedback templates
- Numerical ratings
- Performance scores

---

## 4. Continuous feedback

### Decision

Users can submit feedback at any time.

### Why

The closer feedback is captured to the event that triggered it, the less likely important context is lost. The retrospective becomes the sense-making and decision-making layer rather than a deadline-driven survey.

### MVP

- Continuous submissions
- Feedback history
- Each user can see their own submissions

### Excluded

- Mandatory weekly forms
- Complicated recurring surveys

---

## 5. Privacy

### Decision

Identified by default, anonymous by explicit choice.

### Why

Identification promotes accountability, while optional anonymity provides a channel for sensitive feedback.

### MVP rules

- A contributor sees only their own raw feedback.
- Facilitator can see relevant feedback for the team/projects.
- Facilitator can see the author of anonymous feedback.
- Other team members do not browse others' raw feedback.

### Excluded

- Public feedback feeds
- Peer-to-peer browsing of raw feedback

---

## 6. AI theme generation

### Decision

AI automatically proposes aggregated themes.

### Why

With potentially many submissions, manual aggregation would create significant facilitator work. AI provides real product value by identifying patterns and proposing concise themes.

Example:

> Feedback: “Requirements keep changing.”
>
> Feedback: “We don't get enough clarity before development.”
>
> Feedback: “Product changes scope mid-sprint.”
>
> AI theme: **Requirements and scope clarity**

### Excluded

- AI performance evaluation
- AI employee scoring
- AI deciding what the team must do
- Autonomous AI facilitation

---

## 7. Theme curation

### Decision

The facilitator has complete control.

### Facilitator can

- Edit themes
- Merge themes
- Split themes
- Delete themes
- Create new themes
- Change descriptions
- Associate/dissociate supporting feedback

### Why

AI can identify patterns but may misunderstand organizational context. The facilitator should be the final authority over the retrospective agenda.

---

## 8. Voting

### Decision

Vote on aggregated themes, not individual feedback.

Each team member gets **3 votes per retrospective**.

They can:

- Put all 3 votes on one theme
- Split votes across themes

Votes are facilitator-visible.

### Why

Theme-level voting identifies what the team considers important rather than turning individual comments into popularity contests. Three votes provide prioritization without creating a complicated voting system.

### Threshold

**≥3 votes = discussion eligible**

The threshold makes a theme eligible; it does not force the facilitator to discuss it.

### Excluded

- Ranked-choice voting
- Unlimited votes
- Configurable voting systems
- Multiple voting rounds

---

## 9. Retrospective

### Decision

One weekly team retrospective.

### Why

Feedback is continuous, but the team needs a predictable moment to synthesize it and make decisions.

### Facilitator sees

1. Highest-priority themes
2. Vote counts
3. Supporting feedback
4. Team/project context

The facilitator controls the discussion agenda.

### Excluded

- Separate retrospective engines for every project
- Daily retrospectives
- Asynchronous voting rounds

---

## 10. Facilitator

### Decision

One designated facilitator per team.

The facilitator can be the project owner.

### Why

Someone needs clear ownership of preparing the retrospective, managing themes, facilitating discussion, and ensuring actions are followed up.

### Facilitator capabilities

- Curate themes
- View underlying feedback
- See anonymous authors
- Manage voting
- Lead discussion
- Capture decisions
- Create actions

### Excluded

- Multiple facilitators
- Facilitator hierarchies
- Organization administrators

---

## 11. Discussion capture

### Decision

Capture structured retrospective notes rather than trying to record everything.

For each discussed theme:

- Discussion notes
- Key observations
- Decision
- Actions

### Why

The goal is not to create another meeting-transcription application. The valuable artifact is what the team learned and what it decided to do.

### Excluded

- Video recording
- Audio recording
- Automatic meeting transcription

---

## 12. Decisions

### Decision

Decisions are separate from actions.

### Decision record

- Decision
- Context/rationale
- Date
- Optional decision owner

### Why

A decision describes what the team agreed upon. An action describes what someone needs to execute. Separating them makes historical retrospectives easier to understand.

---

## 13. Actions

### Decision

Every action has:

- Action description
- Owner
- Due date
- Status
- Optional expected outcome
- Optional actual outcome

### Why

Owner + due date + status makes the action operationally trackable. Outcome fields allow the team to determine whether the change actually improved the situation.

This supports:

**Problem → Action → Result → Next retrospective**

### Excluded

- Full project-management functionality
- Dependencies
- Gantt charts
- Sophisticated workflows

---

## 14. Follow-up

### Decision

Previous actions automatically appear in the next retrospective.

### Why

Without follow-up, retrospectives become repetitive conversations where the same problems are discussed every week.

The facilitator should see:

**Previous action → Status → Outcome → Follow-up discussion**

---

## 15. Notifications

### Decision

Minimal notifications.

### MVP notifications

- Upcoming retrospective
- Assigned action
- Action due/overdue

### Why

Notifications support adoption, but a sophisticated notification system is unnecessary before we know which events actually matter.

### Excluded

- Slack/Teams notifications
- Complex notification rules
- Digest engines

---

## 16. Integrations

### Decision

No external integrations in MVP.

### Why

Integrating Jira, GitHub, Linear, Slack, Teams, etc. would dramatically increase development scope before validating the fundamental workflow.

Feedback is entered directly into the application.

### Excluded

- Jira
- GitHub
- Linear
- Asana
- Slack
- Microsoft Teams
- Google Workspace integrations

---

## 17. Analytics

### Decision

Basic product/team analytics, not employee analytics.

### MVP analytics

- Number of feedback submissions
- Themes over time
- Votes
- Open/completed actions
- Recurring themes
- Project vs. team feedback

### Why

These metrics help determine whether the retrospective process is improving. Employee-level performance analytics would change the nature of the product.

### Excluded

- Employee performance scores
- Productivity scores
- Employee rankings
- Employee sentiment scores
- Performance predictions

---

## 18. Technology/product surface

### Decision

Responsive web application.

### Why

One web application is sufficient for the MVP and works across desktop/tablet without maintaining separate mobile applications.

### Excluded

- Native iOS application
- Native Android application

---

# Final MVP Definition

> **A web application for one team managing multiple projects that allows members to continuously submit structured, identified or anonymous feedback; uses AI to aggregate that feedback into themes; allows a facilitator to curate and prioritize those themes through three-vote weighted voting; and turns the highest-priority themes into facilitated retrospective discussions, decisions, and trackable actions.**

## Core workflow

```text
One Team
   |
   +-- Multiple Projects
           |
           v
Continuous Feedback
   |
   +-- What worked?
   +-- What didn't work?
   +-- Start
   +-- Stop
   +-- Continue
   |
   v
AI Theme Generation
   |
   v
Facilitator Curates Themes
   |
   v
Team Voting
   |
   +-- 3 votes per member
   +-- Weighted voting allowed
   +-- Votes visible to facilitator
   |
   v
>= 3 votes
   |
   v
Weekly Retrospective
   |
   +-- Drill into supporting feedback
   +-- Facilitator-led discussion
   |
   +----------+----------+
   |                     |
   v                     v
Decisions              Actions
                       |
                       +-- Owner
                       +-- Due date
                       +-- Status
                       +-- Expected outcome (optional)
                       +-- Actual outcome (optional)
                       |
                       v
                 Next Retrospective
```
