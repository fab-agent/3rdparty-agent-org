# 3rdParty Agent Organization

Self-hosted, open-source platform for companies to manage AI agents in a structured way.

Assign model + skills + policies to each personnel member, visualize the org chart, and sync all configuration to Git via YAML files.

---

## Features

| Feature | Status |
|---|---|
| Multi-company management | ✅ |
| Department + personnel CRUD | ✅ |
| Agent configuration (model, skills, status) | ✅ |
| Org chart visualization (tree view) | ✅ |
| AI provider key management (Anthropic, OpenAI, Google, Mistral) | ✅ |
| Git integration (GitHub / GitLab / Gitea) | ✅ |
| CLI setup wizard (`3pa init`) | ✅ |
| Multi-language support (TR / EN / DE / ES) | ✅ |

---

## Quick Start

### Requirements

- Docker + Docker Compose **or** Python 3.11+ and Node.js 20+
- (Optional) AI provider API key: Anthropic / OpenAI / Google / Mistral

---

### Option A — Docker (Recommended)

```bash
git clone https://github.com/fab-agent/3rdparty-agent-org.git
cd 3rdparty-agent-org

cp .env.example .env
# Edit .env (AI keys, optional)

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

### Option C — CLI Wizard

```bash
cd packages/cli
npm install
npm run build

# Start the wizard
npx 3pa init
```

Step-by-step prompts:
1. Company name + industry
2. AI provider selection and API key entry
3. Git integration (optional)
4. Start the application

---

## After Initial Setup

The platform ships with sample data on first launch:

- **Fabrika Yazılım** — 6 departments, 10 humans, 9 agents
- **Demo Corp** — 1 department, 3 people, 1 agent

Use this data as a template or delete it.

---

## Usage Guide

### 1. Company Management

The active company is shown in the sidebar (bottom left).  
Click the company name to switch between companies or create a new one with the **"Add Company"** button.

Each company has its own departments, personnel, and agents.

---

### 2. Department Management

On the **Departments** page:
- Add a new department (name, slug, description, goals, policies)
- Edit / delete existing departments
- Set department status to Active / Inactive

Policy lists can be defined per department (e.g. "Code Review SLA", "Deployment Approval Policy").

---

### 3. Personnel Management

The **Personnel** page lists both human employees and agents.

When adding new personnel:
- **Type:** Human or Agent
- Assign a **department** and **manager**
- For agents, an `AgentConfig` is automatically created in the background

---

### 4. Agent Configuration

To configure an agent for a personnel member:
1. Select the personnel → `PATCH /personnel/{id}/agent-config`
2. Choose a **model** (claude-sonnet-4-6, gpt-4o, gemini-2.5-pro, ...)
3. Set the **model version** and **status** (draft / active / inactive)
4. Add **skills**: name, version, short description

---

### 5. Org Chart

The **Org Chart** page displays the active company's hierarchy as a tree.  
Click an agent node to view its model, skill list, and responsible person in the right panel.

---

### 6. AI Provider Management

Under **Settings → AI Providers**:

| Provider | Test Support |
|---|---|
| Anthropic (Claude) | ✅ |
| OpenAI (GPT) | ✅ |
| Google (Gemini) | ✅ |
| Mistral | ✅ |

After entering an API key, use the **Test** button to verify it.  
Keys are stored encrypted with AES-256 (Fernet) — never returned as plain text.

---

### 7. Git Integration

Under **Settings → Git Integration**:

1. Select a **provider**: GitHub / GitLab / Gitea
2. Enter the **repo URL**, **branch**, and **access token**
3. Click **Connect**

Once connected:
- **Pull** — Import YAML files from the repo into the database
- **Push** — Export the database to YAML files and commit
- **Diff** — View pending changes
- **Auto PR** — Open a pull request instead of pushing directly (optional)

YAML format (`agents/codeguard/agent.yaml`):
```yaml
id: codeguard
name: CodeGuard
title: Code Review Agent
model: claude-sonnet-4-6
model_version: '4.6'
status: active
department: yazilim-gelistirme
responsible: elif-yildiz
skills:
  - name: Code Review
    version: '2.1'
    description: PR review and security scanning
updated_at: '2026-06-01'
```

---

### 8. Language Switching

Use the flag icon in the top right to change the UI language:  
🇹🇷 Turkish · 🇬🇧 English · 🇩🇪 German · 🇪🇸 Spanish

---

## Architecture

```
3rdparty-agent-org/
├── backend/                    # FastAPI + SQLModel (SQLite)
│   ├── main.py                 # App startup, router registration
│   ├── models.py               # SQLModel tables
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── database.py             # Engine + session
│   ├── seed.py                 # Sample data (2 companies, 7 depts, 19 personnel)
│   ├── api/
│   │   ├── companies.py        # Company CRUD + stats
│   │   ├── departments.py      # Department CRUD
│   │   ├── personnel.py        # Personnel + agent config + skill CRUD
│   │   ├── providers.py        # AI provider key management
│   │   └── git_sync.py         # Git pull/push/diff/logs
│   ├── core/
│   │   └── security.py         # Fernet encryption
│   └── services/
│       ├── provider_service.py # Provider testing + model listing
│       └── git_service.py      # GitPython operations + YAML export/import
│
├── frontend/                   # SvelteKit 5 + Tailwind
│   └── src/
│       ├── lib/
│       │   ├── api/            # Type-safe fetch clients
│       │   ├── components/ui/  # Bespoke components (Button, Dialog, Badge...)
│       │   ├── i18n/           # TR/EN/DE/ES translation dictionaries
│       │   └── stores/         # company.svelte.ts (active company)
│       └── routes/
│           ├── +layout.svelte  # Company switcher, language selector, nav
│           ├── departments/    # Department management
│           ├── personnel/      # Personnel + agent list
│           ├── org-chart/      # Visual org chart
│           └── settings/       # AI providers + Git
│
├── packages/cli/               # `3pa` CLI wizard (TypeScript)
├── data/                       # SQLite DB + Git repo cache
└── docker-compose.yml
```

### Data Model

```
Company ──< Department ──< Personnel ──── AgentConfig ──< Skill
                    │                           │
                    └── (company_id FK)         └── (responsible_id → Personnel)
```

---

## API Reference

Full documentation when the server is running:

- Swagger UI → `http://localhost:8000/docs`
- ReDoc → `http://localhost:8000/redoc`

### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/companies` | Company list + stats |
| POST | `/companies` | Create company |
| GET | `/departments?company_id=` | Department list (filtered by company) |
| GET | `/personnel?company_id=` | Personnel list (filtered by company) |
| GET | `/org-tree?company_id=` | Hierarchical tree |
| GET | `/providers/status` | AI provider statuses |
| POST | `/providers/{p}/key` | Save API key |
| POST | `/providers/{p}/test` | Test API key |
| GET | `/git/config` | Git connection settings |
| POST | `/git/pull` | Pull from repo |
| POST | `/git/push` | Push to repo |

---

## Environment Variables

Start by copying `.env.example`:

```bash
# AI Providers (optional — can also be added from the Settings page)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
MISTRAL_API_KEY=...

# Frontend
VITE_API_URL=http://localhost:8000
```

---

## Development

```bash
# Backend type check (optional)
cd backend && mypy .

# Frontend type check
cd frontend && npm run check

# Frontend build only
cd frontend && npm run build
```

---

## License

MIT — Free for commercial use, forking, and contributions.
