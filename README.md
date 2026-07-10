# 3rdParty Agent Organization

Self-hosted, open-source platform for companies to manage AI agents in a structured way.

Define AI agents per personnel, manage skills and policies via Markdown, visualize the org chart, and onboard your entire organization with a single AI-assisted conversation.

---

## Features

| Feature | Status |
|---|---|
| Multi-company management | ✅ |
| Department + personnel CRUD | ✅ |
| Agent configuration (model, skills, status) | ✅ |
| **AI Onboarding** — web search + AI chat → full org structure in minutes | ✅ |
| **Company Skills Library** — Markdown-based skill definitions assignable to multiple agents | ✅ |
| **Policies Management** — company / department / agent-scoped policies with Markdown editor | ✅ |
| Org chart visualization (interactive tree view) | ✅ |
| AI provider key management (Anthropic, OpenAI, Google, Mistral, Qwen) | ✅ |
| Agent-to-Agent (A2A) delegation with human approval | ✅ |
| Real-time AI chat sessions (SSE streaming) | ✅ |
| First-time setup wizard (no hardcoded credentials) | ✅ |
| JWT auth + bcrypt passwords + AES-256 key encryption | ✅ |
| Audit log | ✅ |
| Multi-language support (TR / EN) | ✅ |
| Company-level authorization (multi-company users) | ✅ |
| Structured JSON logging (logs/app.log) | ✅ |
| Database migrations (Alembic) | ✅ |
| Login rate limiting (Nginx) | ✅ |
| On-demand backup to S3/R2/MinIO (Settings → Backup) | ✅ |
| Social media agent skills (Instagram Business + WhatsApp Cloud API) | ✅ |

---

## AI Onboarding

The standout feature. Instead of manually setting up departments, agents, skills and policies one by one, a conversational AI assistant does it for you:

1. **Web Search** — the system automatically researches your company online for context
2. **Guided Chat** — the AI asks 3–5 targeted questions about your team size, recurring workflows, tools used, and data sensitivity constraints
3. **Preview** — a complete org structure is generated and shown before anything is written to the database
4. **One-click Create** — departments, human personnel, AI agents, skills (with full Markdown content), and policies are all created in a single transaction

The "Create" button only appears after the AI confirms it has gathered sufficient information — preventing premature generation.

To start: **Settings → AI ile Kur** (requires at least one active AI provider key).

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
# Edit .env — JWT_SECRET is required, AI provider keys are optional

docker compose up --build
```

UI → `http://localhost:5173`  
API → `http://localhost:8000`

**Production (with Nginx rate limiting):**

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

UI + API → `http://localhost` (Nginx on port 80)  
Login endpoint is rate-limited to 5 attempts/minute per IP.

---

### Option B — Manual (Development)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

**Frontend (separate terminal):**

```bash
cd frontend
npm install
cp .env.example .env          # VITE_API_URL=http://localhost:8000
npm run dev                   # http://localhost:5173
```

---

### Option C — HTTPS with Cloudflare Tunnel (Recommended for Production)

No port forwarding or SSL certificates needed. Cloudflare Tunnel handles everything.

```bash
# 1. Install cloudflared
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared

# 2. Login and create tunnel
cloudflared tunnel login
cloudflared tunnel create my-org-platform

# 3. Create config at ~/.cloudflared/config.yml
cat > ~/.cloudflared/config.yml << EOF
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: app.your-domain.com
    service: http://localhost:80
  - service: http_status:404
EOF

# 4. Route DNS (automatic)
cloudflared tunnel route dns my-org-platform app.your-domain.com

# 5. Start (or run as a service)
cloudflared tunnel run my-org-platform
```

Update `VITE_API_URL` in `backend/.env` to `https://app.your-domain.com` before rebuilding.

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

### 1. AI Onboarding (Recommended First Step)

Go to **Settings → AI ile Kur**. The wizard:
1. Searches the web for your company
2. Asks you questions about your team and workflows
3. Generates a preview of the org structure
4. Creates everything with one click

Requires at least one active AI provider key in **Settings → AI Providers**.

---

### 2. Company Management

The active company is shown in the sidebar (bottom left).  
Switch between companies or create a new one with the **"Add Company"** button.

Each company has its own departments, personnel, agents, skills, and policies.

---

### 3. Department Management

On the **Departments** page:
- Add a new department (name, slug, description, goals, policies)
- Edit / delete existing departments
- Set department status to Active / Inactive

---

### 4. Personnel Management

The **Personnel** page lists both human employees and agents.

When adding new personnel:
- **Type:** Human or Agent
- Assign a **department** and **manager**
- For agents, an `AgentConfig` is created automatically

---

### 5. Agent Configuration

On the **Agents** page:
1. Choose a **model** (claude-sonnet-4-6, gpt-4o, gemini-2.5-pro, qwen-max, ...)
2. Set **status** (draft / active / inactive)
3. Assign **skills** from the company skills library — checkboxes show all available skills with pre-selection for onboarding-linked ones

---

### 6. Skills Library

On the **Skills** page (`/skills`):
- Create company-wide skill definitions with full Markdown content
- Each skill has a structured template: purpose, usage steps, input/output format, example, guardrails
- Assign skills to one or more agents via `AgentSkillLink`
- Skills created during AI Onboarding appear here automatically

---

### 7. Policies

On the **Policies** page (`/policies`):
- Create policies scoped to **company**, **department**, or **agent**
- Full Markdown editor with structured sections (purpose, scope, rules, rationale, exceptions, compliance)
- Policies created during AI Onboarding appear here automatically

---

### 8. Org Chart

The **Org Chart** page (`/org-chart`) shows the full personnel hierarchy as an interactive tree.  
Click any agent node to open a detail panel with model, status, assigned skills, and linked policies.

---

### 9. Agent-to-Agent (A2A) Delegation

An agent can request a task from another agent. A designated human must approve before execution, and again after reviewing the result.

Flow: `create → pending_approval → approved → running → pending_result_approval → completed`

Rejection is available at both approval stages.

---

### 10. AI Provider Management

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
│   ├── database.py             # Engine + session
│   ├── api/
│   │   ├── auth.py             # Login, invite, setup wizard, JWT
│   │   ├── companies.py        # Company CRUD + stats
│   │   ├── departments.py      # Department CRUD + tree
│   │   ├── personnel.py        # Personnel + agent config + org-tree
│   │   ├── skills.py           # CompanySkill CRUD + AgentSkillLink assign/unassign
│   │   ├── policies.py         # Policy CRUD
│   │   ├── onboarding.py       # AI Onboarding (search / chat / generate / create)
│   │   ├── sessions.py         # AI sessions + SSE streaming
│   │   ├── a2a.py              # Agent-to-Agent delegation flow
│   │   ├── providers.py        # AI provider key management
│   │   ├── dashboard.py        # Live telemetry + personal stats
│   │   └── audit.py            # Audit log
│   ├── core/
│   │   └── security.py         # Fernet encryption (data/.secret)
│   ├── services/
│   │   ├── agent_runtime.py    # AI execution engine (multi-provider)
│   │   ├── onboarding_agent.py # Web search + LLM conversation + bulk org creation
│   │   ├── provider_service.py # Provider testing + model listing
│   │   └── auth.py             # JWT + bcrypt helpers
│   └── migrations/             # Alembic migration scripts
│
└── frontend/                   # SvelteKit 5 + Tailwind
    └── src/
        ├── lib/
        │   ├── api/            # Type-safe fetch clients (personnel, skills, policies, onboarding...)
        │   ├── components/ui/  # Bespoke UI components (Button, Dialog, Badge, Table...)
        │   ├── i18n/           # TR / EN translation dictionaries
        │   └── stores/         # authStore, companyStore
        └── routes/
            ├── setup/          # First-time setup wizard
            ├── onboarding/     # AI Onboarding wizard (search → chat → preview → create)
            ├── agents/         # Agent list + config + company skill assignment
            ├── skills/         # Company skills library + Markdown editor
            ├── policies/       # Policy management + Markdown editor
            ├── org-chart/      # Interactive org tree with agent detail panel
            ├── personnel/      # Personnel list
            ├── departments/    # Department management
            └── settings/       # AI providers, social media, backup, AI Onboarding trigger
```

### Data Model

```
Company ──< Department ──< Personnel ──── AgentConfig ──< AgentSkillLink ──> CompanySkill
                                 │              │
                                 │         AgentSession ──< SessionMessage
                                 │
                          A2ARequest (from_agent → to_agent, human approver)
                          OnboardingSession (progress saved during AI Onboarding)
                          Policy (scope: company | department | agent)
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

---

## TODO

### Security
- [x] Login rate limiting — 5 req/min per IP via Nginx
- [x] Company-level authorization — all endpoints verify caller is a member of the target company
- [x] Input validation — auth endpoints use Pydantic schemas
- [x] `must_change_password` gate — frontend redirects to `/set-password` on first login
- [ ] CORS tightening — `allow_origins=["*"]` should be restricted in production
- [ ] Invite role validation — restrict `founder` role assignment to founders only
- [ ] A2A approver verification — verify JWT caller matches `approver_id`

### Features
- [x] AI Onboarding — full org setup via web search + AI conversation
- [x] Company Skills Library — Markdown-based, assignable to multiple agents
- [x] Policies Management — scoped to company / department / agent
- [x] Org Chart — interactive personnel hierarchy tree
- [x] Social media agent — `instagram_post` + `whatsapp_send` builtin skills
- [x] Backup UI — Settings → Backup tab: S3/R2/MinIO config, on-demand backup
- [ ] Onboarding session resume after browser close (currently persisted, UI resume in progress)
- [ ] Change request workflow for skills and policies

### Infrastructure
- [x] Database migrations — Alembic
- [x] Structured logging — JSON log file at `logs/app.log`, 30-day rotation
- [x] Nginx rate limiting — production docker-compose with brute-force protection
- [x] Cloudflare Tunnel guide — HTTPS setup documented in README
- [ ] PostgreSQL support — swap SQLite for Postgres for concurrent workloads

---

## License

MIT — Free for commercial use, forking, and contributions.
