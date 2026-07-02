# 3rdParty Agent Organization

Self-hosted, open-source platform for companies to manage AI agents in a structured way.

Assign model + skills + policies to each personnel member, visualize the org chart, and manage agent-to-agent (A2A) delegation workflows.

---

## Features

| Feature | Status |
|---|---|
| Multi-company management | ✅ |
| Department + personnel CRUD | ✅ |
| Agent configuration (model, skills, status) | ✅ |
| Org chart visualization (tree view) | ✅ |
| AI provider key management (Anthropic, OpenAI, Google, Mistral, Qwen) | ✅ |
| Agent-to-Agent (A2A) delegation with human approval | ✅ |
| Real-time AI chat sessions (SSE streaming) | ✅ |
| First-time setup wizard (no hardcoded credentials) | ✅ |
| JWT auth + bcrypt passwords + AES-256 key encryption | ✅ |
| Audit log | ✅ |
| Multi-language support (TR / EN) | ✅ |
| Unit test suite (89 tests) | ✅ |

---

## Quick Start

### Requirements

- Docker + Docker Compose **or** Python 3.11+ and Node.js 20+
- (Optional) AI provider API key: Anthropic / OpenAI / Google / Mistral / Qwen

---

### Option A — Docker (Recommended)

```bash
git clone https://github.com/fab-agent/3rdparty-agent-org.git
cd 3rdparty-agent-org

cp backend/.env.example backend/.env
# Edit .env (JWT_SECRET required, AI keys optional)

docker compose up --build
```

UI → `http://localhost:5173`  
API → `http://localhost:8000`

---

### Option B — Manual (Development)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend (separate terminal):**

```bash
cd frontend
npm install
cp .env.example .env          # VITE_API_URL=http://localhost:8000
npm run dev                   # http://localhost:5173
```

---

## First Launch

On first open, a setup wizard asks for:
- Full name
- Company name
- E-mail
- Password

This creates the founder account. No hardcoded credentials — every install gets its own admin.

---

## Usage Guide

### 1. Company Management

The active company is shown in the sidebar (bottom left).  
Switch between companies or create a new one with the **"Add Company"** button.

Each company has its own departments, personnel, and agents.

---

### 2. Department Management

On the **Departments** page:
- Add a new department (name, slug, description, goals, policies)
- Edit / delete existing departments
- Set department status to Active / Inactive

---

### 3. Personnel Management

The **Personnel** page lists both human employees and agents.

When adding new personnel:
- **Type:** Human or Agent
- Assign a **department** and **manager**
- For agents, an `AgentConfig` is created automatically

---

### 4. Agent Configuration

1. Select the personnel → `PATCH /personnel/{id}/agent-config`
2. Choose a **model** (claude-sonnet-4-6, gpt-4o, gemini-2.5-pro, qwen-max, ...)
3. Set **status** (draft / active / inactive)
4. Add **skills**: name, version, description

---

### 5. Agent-to-Agent (A2A) Delegation

An agent can request a task from another agent. A designated human must approve before execution, and again after reviewing the result.

Flow: `create → pending_approval → approved → running → pending_result_approval → completed`

Rejection is available at both approval stages.

---

### 6. AI Provider Management

Under **Settings → AI Providers**:

| Provider | Models |
|---|---|
| Anthropic (Claude) | claude-opus-4-8, claude-sonnet-4-6, claude-haiku-4-5 |
| OpenAI (GPT) | gpt-4o, gpt-4o-mini, o1, o3-mini |
| Google (Gemini) | gemini-2.5-pro, gemini-2.0-flash |
| Mistral | mistral-large, mistral-small, codestral |
| Alibaba Qwen | qwen-max, qwen-plus, qwen-turbo, qwen-long |

After entering an API key the system tests it immediately.  
Keys are stored encrypted with AES-256 (Fernet) — never returned as plain text.

---

## Architecture

```
3rdparty-agent-org/
├── backend/                    # FastAPI + SQLModel (SQLite)
│   ├── main.py                 # App startup, router registration
│   ├── models.py               # SQLModel tables
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── database.py             # Engine + session (expire_on_commit=False)
│   ├── seed.py                 # Sample org data (no user creation)
│   ├── api/
│   │   ├── auth.py             # Login, invite, setup wizard, JWT
│   │   ├── companies.py        # Company CRUD + stats
│   │   ├── departments.py      # Department CRUD + tree
│   │   ├── personnel.py        # Personnel + agent config + skill CRUD
│   │   ├── sessions.py         # AI sessions + SSE streaming
│   │   ├── a2a.py              # Agent-to-Agent delegation flow
│   │   ├── providers.py        # AI provider key management
│   │   └── audit.py            # Audit log
│   ├── core/
│   │   └── security.py         # Fernet encryption (data/.secret)
│   ├── services/
│   │   ├── agent_runtime.py    # AI execution engine (Anthropic / OpenAI / Google / Mistral / Qwen)
│   │   ├── provider_service.py # Provider testing + model listing
│   │   └── auth.py             # JWT + bcrypt helpers
│   └── tests/                  # 89 pytest unit + integration tests
│
└── frontend/                   # SvelteKit 5 + Tailwind
    └── src/
        ├── lib/
        │   ├── api/            # Type-safe fetch clients
        │   ├── components/ui/  # Bespoke UI components (Button, Dialog, Badge...)
        │   ├── i18n/           # TR / EN translation dictionaries
        │   └── stores/         # authStore, companyStore
        └── routes/
            ├── setup/          # First-time setup wizard
            ├── +layout.svelte  # Auth guard, nav, language selector
            ├── organizations/  # Company management
            ├── personnel/      # Personnel + agent list
            └── settings/       # AI providers
```

### Data Model

```
Company ──< Department ──< Personnel ──── AgentConfig ──< Skill
                                 │
                          A2ARequest (from_agent → to_agent, human approver)
                          AgentSession ──< SessionMessage
```

---

## API Reference

Full docs when the server is running:

- Swagger UI → `http://localhost:8000/docs`
- ReDoc → `http://localhost:8000/redoc`

All endpoints require `Authorization: Bearer <token>` except `/auth/token`, `/auth/setup-status`, and `/auth/setup`.

---

## Environment Variables

```bash
# Required
JWT_SECRET=<random-64-char-hex>

# Email (optional — needed for invite/reset flows)
RESEND_API_KEY=
EMAIL_FROM=noreply@example.com
APP_URL=http://localhost:5173

# AI Providers (optional — can also be added from the Settings page)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
MISTRAL_API_KEY=...
QWEN_API_KEY=sk-...
```

---

## Testing

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

89 tests covering: auth, providers, A2A flow, agent runtime, CRUD endpoints.

---

## TODO

### Security
- [ ] **Login rate limiting** — brute-force protection on `POST /auth/token`. Implement via `slowapi` or upstream Nginx/Caddy limit_req.
- [ ] **CORS tightening** — `allow_origins=["*"]` is fine for self-hosted dev but should be restricted to the frontend URL in production deployments.
- [ ] **Invite role validation** — currently a `dept_head` (manager) can invite someone with the `founder` role. Restrict: only founders can assign the founder role.
- [ ] **A2A approver caller verification** — `POST /a2a/requests/{id}/approve` checks that `body.approver_id` matches `req.approver_id`, but does not yet verify that the JWT caller's personnel record matches `approver_id`. Needs `Personnel.user_id == caller.id` check.
- [ ] **Email format validation** — `POST /auth/invite` and `POST /auth/setup` accept any string as email. Add regex or `email-validator` check.

### Features
- [ ] **Qwen end-to-end test** — DashScope API key required. Get a valid key from [console.aliyun.com](https://dashscope.aliyuncs.com) and test via Settings → AI Providers.
- [ ] **Faz 2: Markdown editors** — `company.md` (company policy editor), `agent.md` (agent persona editor), `policy.md` per department.
- [ ] **Org chart frontend** — personnel hierarchy tree visualization page.
- [ ] **A2A inbox UI** — frontend page to list pending A2A approvals for the logged-in user.
- [ ] **Session history UI** — browse and replay past agent sessions.
- [ ] **must_change_password gate** — frontend should redirect to change-password page when `must_change_password: true` is returned from `/auth/me`.

### Infrastructure
- [ ] **PostgreSQL support** — swap SQLite for Postgres for multi-user concurrent workloads.
- [ ] **Docker health checks** — add `HEALTHCHECK` to backend and frontend Dockerfile.
- [ ] **`.env.example`** — create committed example file so new contributors know what vars are needed.

---

## License

MIT — Free for commercial use, forking, and contributions.
