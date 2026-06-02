# fab.engineering

**Self-hosted platform for managing agentic organizations.**

We're building the infrastructure layer that lets companies define, deploy, and govern AI agents as first-class members of their org chart — with policies, skills, approval flows, and human oversight built in from day one.

---

## What We're Building

Most companies experimenting with AI agents today are doing it ad-hoc: scattered prompts, no governance, no visibility. We think that's a problem.

`fab.engineering` gives organizations a structured way to run agentic operations:

- **Agent Personnel** — Every AI agent has a name, a role, a department, a responsible human, and a set of skills. It lives in the org chart like anyone else.
- **Policy Management** — Agents operate within defined policies. Changes go through a review and approval flow before taking effect.
- **Autonomous Flows** — Scheduled tasks that run agents on a cron, deliver results to the inbox, and keep humans informed without requiring manual triggers.
- **Task Requests** — Anyone in the org can request an agent for a task. The system routes to the best match based on department and skill, notifies the responsible human, and tracks the outcome.
- **Change Requests** — Agent configuration changes follow a two-stage approval chain (department head → admin) before being committed to version control.
- **Inbox** — A unified notification layer where flow results, task completions, and system events land for the right people.

---

## Design Philosophy

**Human oversight, not human bottlenecks.** Agents operate autonomously, but every critical action — config changes, new deployments, task execution — has a defined approval path and an audit trail.

**Self-hosted first.** Companies keep their data, their keys, and their agent configurations on their own infrastructure. No SaaS lock-in.

**Org-native.** Agents aren't tools. They're personnel. They belong to departments, have managers, carry policies, and appear in the org chart.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · SQLModel · SQLite · APScheduler |
| Frontend | SvelteKit 5 · Tailwind CSS |
| AI | Anthropic · OpenAI · Google · xAI (per-agent config) |
| Version Control | GitHub (Contents API — policy & config sync) |
| Deployment | Docker · Hetzner |

---

## Status

Active development. Core platform (agent management, departments, flows, inbox, change requests) is functional. Tool use, multi-step reasoning, and agent memory are next.

---

<sub>Built by [Fabrika Yazılım](https://fab.limited) · Istanbul</sub>
