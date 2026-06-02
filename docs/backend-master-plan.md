# Backend Master Plan
# 3rdParty Agent — Teknik Yol Haritası

> Oluşturulma: 2026-06-01  
> Durum: Aktif Plan  
> Kapsam: Backend + CLI + Entegrasyonlar

---

## Vizyon Özeti

**3rdParty Agent**, şirketlerin AI ajanlarını, yeteneklerini (skills) ve politikalarını (policies) merkezi, izlenebilir ve versiyonlanmış biçimde yönetmesini sağlayan açık kaynak, self-hosted bir platformdur.

Üç temel katman üzerine inşa edilir:

```
┌─────────────────────────────────────────────────────────────────┐
│  Katman 3 — Git Kabiliyat Deposu                                │
│  Skills, policies ve agent config'ler bir git repo'sunda yaşar  │
│  PR ile değişir, audit trail otomatik gelir                     │
├─────────────────────────────────────────────────────────────────┤
│  Katman 2 — AI Provider Gateway                                 │
│  Anthropic / OpenAI / Google / Mistral anahtarları merkezi      │
│  Hangi anahtarlar aktifse o modeller seçilebilir olur           │
├─────────────────────────────────────────────────────────────────┤
│  Katman 1 — Self-hosted Kurulum                                 │
│  npx @3rdpartyagent/cli init → interaktif sihirbaz              │
│  API key + git bağlantısı + DB → localhost başlatır             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Faz Haritası

| Faz | Başlık | Öncelik | Tahmini Süre |
|-----|--------|---------|--------------|
| F1  | Modüler Backend Refactor | P0 | 1-2 gün |
| F2  | Config & Provider Key Yönetimi | P0 | 2-3 gün |
| F3  | CLI Kurulum Sihirbazı | P0 | 3-4 gün |
| F4  | Git Entegrasyonu (GitHub/GitLab) | P1 | 4-5 gün |
| F5  | Model Registry & Frontend Bağlantısı | P1 | 2-3 gün |
| F6  | Sync Engine & Conflict Resolution | P2 | 3-5 gün |
| F7  | Auth & Multi-user | P2 | 3-4 gün |

---

## F1 — Modüler Backend Refactor

Şu an tüm kod `main.py` içinde. Ölçeklenebilir yapı için bölünmesi gerekiyor.

### Hedef Yapı

```
backend/
├── main.py                  # Sadece app tanımı, middleware, startup
├── models.py                # Tüm SQLModel tanımları
├── schemas.py               # Pydantic request/response modelleri
├── database.py              # engine, get_session, migration helpers
├── seed.py                  # Seed data (main.py'den ayrılır)
├── api/
│   ├── __init__.py
│   ├── departments.py       # /departments CRUD
│   ├── personnel.py         # /personnel CRUD + agent-config + skills
│   ├── providers.py         # /providers status + key yönetimi (F2'de)
│   └── git_sync.py          # /git CRUD + sync trigger (F4'te)
├── core/
│   ├── __init__.py
│   ├── config.py            # Settings (env vars, .env okuma)
│   ├── security.py          # Key şifreleme/şifre çözme, AES-256
│   └── file_manager.py      # MD/YAML dosya I/O (F4'te)
├── services/
│   ├── __init__.py
│   ├── provider_service.py  # API key doğrulama, model listesi çekme
│   └── git_service.py       # clone, pull, push, diff (F4'te)
├── requirements.txt
└── .env.example
```

### Yeni `database.py`

```python
from sqlmodel import create_engine, Session, SQLModel
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    os.makedirs("data", exist_ok=True)
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
```

### Router pattern (`api/departments.py`)

```python
from fastapi import APIRouter, HTTPException
from database import get_session
from models import Department
from schemas import DepartmentCreate, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["departments"])

@router.get("/")
def list_departments():
    with get_session() as session:
        ...

@router.post("/", status_code=201)
def create_department(body: DepartmentCreate):
    ...
```

`main.py`:
```python
from api.departments import router as dept_router
from api.personnel   import router as personnel_router

app.include_router(dept_router)
app.include_router(personnel_router)
```

---

## F2 — Config & Provider Key Yönetimi

### Yeni Modeller

```python
class AppConfig(SQLModel, table=True):
    """Key-value store for platform-wide settings."""
    key:   str = Field(primary_key=True)  # "company_name", "setup_completed", ...
    value: str

class ProviderKey(SQLModel, table=True):
    """Encrypted API keys per AI provider."""
    id:           str = Field(default_factory=uuid4_str, primary_key=True)
    provider:     str                    # "anthropic" | "openai" | "google" | "mistral"
    encrypted_key: str                   # AES-256-GCM ile şifrelenmiş
    status:       str = "unconfigured"   # "active" | "invalid" | "unconfigured"
    last_tested:  datetime | None = None
    created_at:   datetime = Field(default_factory=datetime.utcnow)
```

### Güvenlik: Key Şifreleme

Platform başlatılırken rastgele bir `ENCRYPTION_KEY` üretilir ve `data/.secret` dosyasına yazılır (gitignore'da). Kullanıcı kendi sunucusunda çalıştırdığı için bu yeterlidir.

```python
# core/security.py
from cryptography.fernet import Fernet
import os, pathlib

SECRET_FILE = pathlib.Path("data/.secret")

def get_fernet() -> Fernet:
    if not SECRET_FILE.exists():
        key = Fernet.generate_key()
        SECRET_FILE.write_bytes(key)
        SECRET_FILE.chmod(0o600)
    return Fernet(SECRET_FILE.read_bytes())

def encrypt(plain: str) -> str:
    return get_fernet().encrypt(plain.encode()).decode()

def decrypt(cipher: str) -> str:
    return get_fernet().decrypt(cipher.encode()).decode()
```

### Provider Endpoint'leri

```
GET  /providers/status
     → Her provider için: status, available_models, last_tested

POST /providers/{provider}/key
     body: { "key": "sk-ant-..." }
     → Anahtarı şifreler, test eder, kaydeder

DELETE /providers/{provider}/key
     → Anahtarı siler, status = "unconfigured"

POST /providers/{provider}/test
     → Mevcut anahtarı yeniden test eder

GET  /providers/models
     → Sadece "active" sağlayıcıların modellerini döner
```

### Provider Doğrulama Servisi (`services/provider_service.py`)

```python
PROVIDER_TEST_CONFIGS = {
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "headers": lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01"},
        "body": {"model": "claude-haiku-4-5-20251001", "max_tokens": 1,
                 "messages": [{"role": "user", "content": "hi"}]},
        "models": ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "headers": lambda k: {"Authorization": f"Bearer {k}"},
        "body": {"model": "gpt-4o-mini", "max_tokens": 1,
                 "messages": [{"role": "user", "content": "hi"}]},
        "models": ["gpt-4o", "gpt-4o-mini", "o1-mini"],
    },
    "google": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models",
        "headers": lambda k: {"x-goog-api-key": k},
        "body": None,
        "models": ["gemini-2.5-pro", "gemini-2.0-flash"],
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/models",
        "headers": lambda k: {"Authorization": f"Bearer {k}"},
        "body": None,
        "models": ["mistral-large-latest", "mistral-small-latest"],
    },
}

async def test_provider(provider: str, plain_key: str) -> bool:
    config = PROVIDER_TEST_CONFIGS[provider]
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.get(config["url"], headers=config["headers"](plain_key))
    return resp.status_code in (200, 201)
```

### Frontend Model Seçimi

Ajan oluştururken model dropdown'ı artık mock listeden değil, `/providers/models` endpoint'inden gelir:

```
GET /providers/models
→ [
    { "id": "claude-sonnet-4-6",  "name": "Claude Sonnet 4.6",   "provider": "anthropic" },
    { "id": "gpt-4o",             "name": "GPT-4o",               "provider": "openai" },
    ...  sadece aktif sağlayıcıların modelleri
  ]
```

---

## F3 — CLI Kurulum Sihirbazı

### Paket Yapısı

```
packages/cli/                 ← ayrı npm paketi
├── package.json              # name: "@3rdpartyagent/cli"
├── bin/
│   └── index.js              # #!/usr/bin/env node
└── src/
    ├── commands/
    │   ├── init.ts           # npx @3rdpartyagent/cli init
    │   ├── start.ts          # npx @3rdpartyagent/cli start
    │   └── status.ts         # npx @3rdpartyagent/cli status
    └── utils/
        ├── prompt.ts         # @clack/prompts wrappers
        ├── apiClient.ts      # backend kurulum API'si
        └── envWriter.ts      # .env dosyası yönetimi
```

### `init` Akışı

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   npx @3rdpartyagent/cli init                           │
│                                                         │
│   ┌─ Hoş geldiniz ──────────────────────────────────┐  │
│   │ 3rdParty Agent'ı kuruyorsunuz.                  │  │
│   │ Bu sihirbaz ~2 dakika sürer.                    │  │
│   └──────────────────────────────────────────────────┘  │
│                                                         │
│   [1/5] Şirket bilgileri                                │
│         Şirket adı: ___                                 │
│         Sektör: ___                                     │
│                                                         │
│   [2/5] AI sağlayıcıları                                │
│         ◉ Anthropic (Claude)  → sk-ant-...  ✓           │
│         ◉ OpenAI (GPT)        → sk-...      ✓           │
│         ◯ Google (Gemini)     atlandı                   │
│         ◯ Mistral             atlandı                   │
│                                                         │
│   [3/5] GitHub/GitLab entegrasyonu                      │
│         ◉ GitHub  ◯ GitLab  ◯ Hayır, şimdi değil       │
│         Repo URL: https://github.com/acme/ai-caps       │
│         Token: ghp_...        ✓ Bağlandı                │
│                                                         │
│   [4/5] Sunucu ayarları                                 │
│         Port: [3000]                                    │
│         Veri dizini: [./data]                           │
│                                                         │
│   [5/5] Kurulum tamamlanıyor...                         │
│         ✓ Yapılandırma dosyası yazıldı                  │
│         ✓ Veritabanı oluşturuldu                        │
│         ✓ Örnek veri eklendi                            │
│         ✓ Senkronizasyon başlatıldı                     │
│                                                         │
│   ────────────────────────────────────────────────────  │
│   ✓ Hazır!                                              │
│                                                         │
│   Uygulamayı başlatmak için:                            │
│     npx @3rdpartyagent/cli start                        │
│                                                         │
│   Tarayıcıda aç:                                        │
│     → http://localhost:3000                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### `.env` Çıktısı (init sonrası)

```ini
# 3rdParty Agent — Yapılandırma
# Bu dosyayı paylaşmayın. Otomatik oluşturulmuştur.

COMPANY_NAME="Acme Corp"
COMPANY_SECTOR="Yazılım & SaaS"
PORT=3000

# API Anahtarları (şifreli olarak DB'de de tutulur)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Git Entegrasyonu
GIT_PROVIDER=github
GIT_REPO_URL=https://github.com/acme/ai-capabilities
GIT_TOKEN=ghp_...
GIT_BRANCH=main
GIT_SYNC_INTERVAL=30

# Sistem
DATABASE_URL=sqlite:///./data/app.db
ENCRYPTION_KEY=auto  # data/.secret dosyasından okunur
```

### `package.json` (CLI)

```json
{
  "name": "@3rdpartyagent/cli",
  "version": "0.1.0",
  "description": "3rdParty Agent Platform CLI",
  "bin": {
    "3rdpartyagent": "./bin/index.js"
  },
  "keywords": ["ai", "agents", "self-hosted", "open-source"],
  "dependencies": {
    "@clack/prompts": "^0.7",
    "chalk": "^5",
    "execa": "^8",
    "dotenv": "^16"
  }
}
```

---

## F4 — Git Entegrasyonu

### Kavramsal Model

```
Platform DB  ←──sync──→  Git Repo (şirketin kendi repo'su)
                          ├── skills/
                          │   ├── code-review.yaml
                          │   └── seo.yaml
                          ├── policies/
                          │   ├── security.md
                          │   └── content.md
                          └── agents/
                              └── codeguard/
                                  └── agent.yaml
```

**Pull yönü** (repo → DB): Repo'daki değişiklikler platform DB'ye yansır  
**Push yönü** (DB → repo): Platform'dan yapılan değişiklikler commit + PR olarak git'e gider

### Git Config Modeli

```python
class GitConfig(SQLModel, table=True):
    id:              str = Field(default_factory=uuid4_str, primary_key=True)
    provider:        str                  # "github" | "gitlab" | "gitea"
    repo_url:        str
    branch:          str = "main"
    encrypted_token: str
    sync_interval:   int = 30            # dakika
    auto_pr:         bool = True         # değişikliklerde PR aç
    last_synced:     datetime | None = None
    last_commit_sha: str | None = None
    status:          str = "connected"   # "connected" | "error" | "conflict"

class SyncLog(SQLModel, table=True):
    id:          str = Field(default_factory=uuid4_str, primary_key=True)
    direction:   str                     # "pull" | "push"
    files_changed: int = 0
    commit_sha:  str | None = None
    pr_url:      str | None = None
    status:      str                     # "success" | "error" | "conflict"
    message:     str | None = None
    created_at:  datetime = Field(default_factory=datetime.utcnow)
```

### Git Repo Dosya Formatları

**`skills/code-review.yaml`**
```yaml
id: code-review
name: Code Review
version: "2.1"
description: PR inceleme, best practice kontrolü, güvenlik açığı taraması
tags: [development, security, quality]
maintainer: elif-yildiz
updated_at: "2026-06-01"
```

**`policies/security-policy.md`**
```markdown
---
id: security-policy
name: Güvenlik Politikası
scope: company          # company | department | agent
department: null        # scope=department ise departman slug
version: "1.2"
updated_at: "2026-06-01"
---

# Güvenlik Politikası

## Kapsam
Bu politika tüm AI ajanlarına uygulanır...

## Kurallar
- Hassas veri içeren sorgularda...
```

**`agents/codeguard/agent.yaml`**
```yaml
id: codeguard
name: CodeGuard
title: Code Review Agent
model: claude-sonnet-4-6
status: active
department: yazilim-gelistirme
responsible: elif-yildiz
skills:
  - id: code-review
    version: "2.1"
  - id: typescript
    version: "5.x"
policies:
  - security-policy
  - code-review-sla
```

### Git Endpoint'leri

```
GET    /git/config                  → mevcut git yapılandırması
POST   /git/config                  → yeni bağlantı kur
DELETE /git/config                  → bağlantıyı kopar

POST   /git/sync                    → manuel sync tetikle
GET    /git/sync/logs?limit=20      → sync geçmişi

GET    /git/status                  → diff: DB vs repo
POST   /git/push                    → DB değişikliklerini commit et
POST   /git/pull                    → repo'dan DB'ye çek
```

### Senkronizasyon Servisi

```python
# services/git_service.py

class GitSyncService:
    async def pull(self) -> SyncResult:
        """Repo'dan değişiklikleri çek, DB'yi güncelle."""
        # 1. git pull
        # 2. Değişen YAML/MD dosyalarını tespit et
        # 3. Her dosyayı parse et → DB kayıtlarını upsert et
        # 4. SyncLog yaz

    async def push(self, message: str) -> SyncResult:
        """DB değişikliklerini repo'ya yaz, PR aç."""
        # 1. DB → YAML/MD dosyalarına yaz
        # 2. git add + commit
        # 3. auto_pr=True ise GitHub/GitLab API ile PR aç
        # 4. SyncLog yaz

    async def diff(self) -> list[FileDiff]:
        """DB ile repo arasındaki farkları göster."""
```

### Conflict Çözümü

```
┌────────────────────────────────────────┐
│  Conflict Stratejisi                   │
│                                        │
│  Platform Default: "repo wins"         │
│  → Git repo canonical source of truth │
│  → DB değişiklikleri branch'e gider    │
│  → Merge kararı git üzerinde verilir  │
│                                        │
│  Alternatif: "db wins"                 │
│  → Platform DB canonical              │
│  → Her değişiklik otomatik commit     │
└────────────────────────────────────────┘
```

---

## F5 — Model Registry & Frontend Bağlantısı

### Frontend'de Dinamik Model Seçimi

Ajan oluştururken model dropdown'ı:

```typescript
// src/lib/api/providers.ts
export const providers = {
  status: () => api.get<ProviderStatus[]>('/providers/status'),
  models: () => api.get<ModelDefinition[]>('/providers/models'),
  setKey: (provider: string, key: string) =>
    api.post(`/providers/${provider}/key`, { key }),
  testKey: (provider: string) =>
    api.post(`/providers/${provider}/test`, {}),
};
```

### Settings Sayfası — Provider Yönetimi

```
/settings/providers

┌─ Anthropic (Claude) ──────────────────────────────────────────┐
│  ● Aktif   claude-opus-4-7, claude-sonnet-4-6, claude-haiku   │
│  Son test: 2 dakika önce                    [Test] [Sil Key]  │
└───────────────────────────────────────────────────────────────┘

┌─ OpenAI ──────────────────────────────────────────────────────┐
│  ● Aktif   gpt-4o, gpt-4o-mini, o1-mini                       │
│  Son test: 5 dakika önce                    [Test] [Sil Key]  │
└───────────────────────────────────────────────────────────────┘

┌─ Google (Gemini) ─────────────────────────────────────────────┐
│  ○ Yapılandırılmamış                           [API Key Gir]  │
└───────────────────────────────────────────────────────────────┘
```

---

## F6 — Webhook & Gerçek Zamanlı Sync

Pollingden daha verimli: git provider webhook'u platform'a `POST /git/webhook` atar, platform anında sync yapar.

```python
@router.post("/git/webhook")
async def git_webhook(request: Request, background_tasks: BackgroundTasks):
    # GitHub/GitLab webhook imzasını doğrula
    signature = request.headers.get("x-hub-signature-256")
    verify_signature(await request.body(), signature)
    # Arka planda sync tetikle
    background_tasks.add_task(git_service.pull)
    return {"status": "queued"}
```

---

## F7 — Auth & Multi-user

MVP sonrası. İki seçenek:

**Seçenek A — API Key (basit)**
```python
class ApiKey(SQLModel, table=True):
    key_hash: str = Field(primary_key=True)
    user_id:  str = Field(foreign_key="user.id")
    scopes:   str  # JSON: ["read", "write", "admin"]
    expires_at: datetime | None = None
```

**Seçenek B — JWT (standart)**
- Login endpoint → JWT token (7 günlük)
- Refresh token mekanizması
- Rol tabanlı yetkilendirme (admin / manager / viewer)

Platform self-hosted olduğu için B seçeneği daha uygun — her kurulumun kendi kullanıcı yönetimi olur.

---

## Teknik Borç (Mevcut Durum)

Şu an giderilmesi gereken sorunlar, öncelik sırasıyla:

| # | Sorun | Çözüm | Faz |
|---|-------|-------|-----|
| T1 | `main.py` monolith | Router'lara böl | F1 |
| T2 | DB migration yok | Alembic entegre et | F1 |
| T3 | API key plaintext `.env`'de | ProviderKey modeli + şifreleme | F2 |
| T4 | CORS `allow_origins=["*"]` | Origin whitelist | F7 |
| T5 | Auth yok | JWT (F7) veya API key | F7 |
| T6 | Slug uniqueness kontrolsüz | DB unique constraint + 409 response | F1 |
| T7 | 404/409 eksik | HTTPException standartlaştır | F1 |
| T8 | Query param yerine request body | Pydantic schemas (kısmen yapıldı) | F1 |

---

## Bağımlılıklar

```txt
# requirements.txt (hedef)
fastapi>=0.115
uvicorn[standard]>=0.30
sqlmodel>=0.0.18
pydantic>=2.7
pydantic-settings>=2.3
cryptography>=42           # AES şifreleme
httpx>=0.27                # Provider key testi (async)
gitpython>=3.1             # Git işlemleri
apscheduler>=3.10          # Periyodik sync scheduler
python-multipart>=0.0.9    # Form upload desteği
alembic>=1.13              # DB migration
```

---

## Özet: Ne Zaman Ne Açılıyor

```
F1 tamamlanınca  →  Temiz, sürdürülebilir backend yapısı
F2 tamamlanınca  →  API key'ler güvenli, modeller dinamik seçilebilir
F3 tamamlanınca  →  Açık kaynak kullanıcılar "npx ... init" ile kurabilir
F4 tamamlanınca  →  Skills/policies git'te yaşar, PR ile değişir
F5 tamamlanınca  →  Model dropdown hangi key'ler aktifse onları gösterir
F6 tamamlanınca  →  Git değişiklikleri webhook ile anında platforma yansır
F7 tamamlanınca  →  Çok kullanıcılı, rol tabanlı erişim kontrolü
```

---

*Bu doküman yaşayan bir plandır. Her faz tamamlandıkça güncellenmelidir.*
