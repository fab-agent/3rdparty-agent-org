# 3rdParty Agent Organization

Self-hosted, açık kaynak — şirketlerin yapay zeka ajanlarını organize biçimde yönetmesini sağlayan platform.

Her personele model + skill + policy ataması yapılır; organizasyon şeması görselleştirilir; tüm konfigürasyon YAML dosyaları üzerinden Git'e senkronize edilir.

---

## Özellikler

| Özellik | Durum |
|---|---|
| Çoklu şirket yönetimi | ✅ |
| Departman + personel CRUD | ✅ |
| Ajan yapılandırması (model, skill, status) | ✅ |
| Organizasyon şeması (ağaç görünümü) | ✅ |
| AI sağlayıcı anahtar yönetimi (Anthropic, OpenAI, Google, Mistral) | ✅ |
| Git entegrasyonu (GitHub / GitLab / Gitea) | ✅ |
| CLI kurulum sihirbazı (`3pa init`) | ✅ |
| Çok dil desteği (TR / EN / DE / ES) | ✅ |

---

## Hızlı Başlangıç

### Gereksinimler

- Docker + Docker Compose **veya** Python 3.11+ ve Node.js 20+
- (Opsiyonel) AI sağlayıcı API anahtarı: Anthropic / OpenAI / Google / Mistral

---

### Seçenek A — Docker ile (Önerilen)

```bash
git clone https://github.com/fab-agent/3rdparty-agent-org.git
cd 3rdparty-agent-org

cp .env.example .env
# .env dosyasını düzenle (AI anahtarları, opsiyonel)

docker compose up --build
```

Arayüz → `http://localhost:5173`  
API → `http://localhost:8000`

---

### Seçenek B — Manuel (Geliştirme)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend (ayrı terminalde):**

```bash
cd frontend
npm install
cp .env.example .env          # VITE_API_URL=http://localhost:8000
npm run dev                   # http://localhost:5173
```

---

### Seçenek C — CLI Sihirbazı

```bash
cd packages/cli
npm install
npm run build

# Sihirbazı başlat
npx 3pa init
```

Adım adım yönlendirmeler:
1. Şirket adı + sektör
2. AI sağlayıcı seçimi ve API anahtarı girişi
3. Git entegrasyonu (opsiyonel)
4. Uygulamayı başlat

---

## İlk Kurulumdan Sonra

Platform ilk açılışta örnek veri ile gelir:

- **Fabrika Yazılım** — 6 departman, 10 insan, 9 ajan
- **Demo Corp** — 1 departman, 3 kişi, 1 ajan

Bu verileri şablon olarak kullanabilir ya da silebilirsiniz.

---

## Kullanım Kılavuzu

### 1. Şirket Yönetimi

Kenar çubukta (sol alt) aktif şirket gösterilir.  
Şirkete tıklayarak listeden başka bir şirkete geçiş yapabilir ya da **"Şirket Ekle"** butonu ile yeni şirket oluşturabilirsiniz.

Her şirket kendi departmanlarına, personeline ve ajanlarına sahiptir.

---

### 2. Departman Yönetimi

**Departmanlar** sayfasında:
- Yeni departman ekle (ad, slug, açıklama, hedefler, politikalar)
- Mevcut departmanı düzenle / sil
- Departman durumunu Aktif / Pasif olarak ayarla

Departmanlara bağlı policy listesi tanımlanabilir (örneğin "Code Review SLA", "Deployment Onay Politikası").

---

### 3. Personel Yönetimi

**Personel** sayfasında hem insan çalışanlar hem de ajanlar listelenir.

Yeni personel eklerken:
- **Tür:** İnsan veya Ajan seçilir
- **Departman** ve **yönetici** atanır
- Ajan türündeyse arka planda `AgentConfig` oluşturulur

---

### 4. Ajan Yapılandırması

Bir personelin ajan yapılandırması için:
1. Personeli seçin → `PATCH /personnel/{id}/agent-config`
2. **Model** seçin (claude-sonnet-4-6, gpt-4o, gemini-2.5-pro, ...)
3. **Model versiyonu** ve **durum** belirleyin (draft / active / inactive)
4. **Skill** ekleyin: ad, versiyon, kısa açıklama

---

### 5. Organizasyon Şeması

**Org Haritası** sayfası aktif şirketin hiyerarşisini ağaç yapısında gösterir.  
Bir ajana tıklayarak sağ panelde model, skill listesi ve sorumlu kişiyi görüntüleyebilirsiniz.

---

### 6. AI Sağlayıcı Yönetimi

**Ayarlar → AI Sağlayıcıları** sekmesinde:

| Sağlayıcı | Test Desteği |
|---|---|
| Anthropic (Claude) | ✅ |
| OpenAI (GPT) | ✅ |
| Google (Gemini) | ✅ |
| Mistral | ✅ |

API anahtarı girdikten sonra **Test** butonu ile anahtarın geçerliliği doğrulanır.  
Anahtarlar AES-256 (Fernet) ile şifrelenmiş olarak saklanır — hiçbir zaman düz metin dönmez.

---

### 7. Git Entegrasyonu

**Ayarlar → Git Entegrasyonu** sekmesinde:

1. **Sağlayıcı** seçin: GitHub / GitLab / Gitea
2. **Repo URL**, **branch** ve **access token** girin
3. **Bağlan** butonuna basın

Bağlandıktan sonra:
- **Pull** — Repo'dan YAML dosyalarını veritabanına aktar
- **Push** — Veritabanını YAML dosyalarına çevir ve commit et
- **Farklar** — Bekleyen değişiklikleri görüntüle
- **Otomatik PR** — Push yerine pull request oluşturma (opsiyonel)

YAML formatı (`agents/codeguard/agent.yaml`):
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
    description: PR inceleme ve güvenlik taraması
updated_at: '2026-06-01'
```

---

### 8. Dil Değiştirme

Sağ üst köşede bayrak ikonu ile arayüz dili değiştirilebilir:  
🇹🇷 Türkçe · 🇬🇧 English · 🇩🇪 Deutsch · 🇪🇸 Español

---

## Mimari

```
3rdparty-agent-org/
├── backend/                    # FastAPI + SQLModel (SQLite)
│   ├── main.py                 # Uygulama başlatma, router kaydı
│   ├── models.py               # SQLModel tabloları
│   ├── schemas.py              # Pydantic istek/yanıt şemaları
│   ├── database.py             # Engine + session
│   ├── seed.py                 # Örnek veri (2 şirket, 7 dept, 19 personel)
│   ├── api/
│   │   ├── companies.py        # Şirket CRUD + istatistikler
│   │   ├── departments.py      # Departman CRUD
│   │   ├── personnel.py        # Personel + ajan config + skill CRUD
│   │   ├── providers.py        # AI sağlayıcı anahtar yönetimi
│   │   └── git_sync.py         # Git pull/push/diff/logs
│   ├── core/
│   │   └── security.py         # Fernet şifreleme
│   └── services/
│       ├── provider_service.py # Sağlayıcı test + model listesi
│       └── git_service.py      # GitPython işlemleri + YAML dışa/içe aktarma
│
├── frontend/                   # SvelteKit 5 + Tailwind
│   └── src/
│       ├── lib/
│       │   ├── api/            # Tip güvenli fetch istemcileri
│       │   ├── components/ui/  # Bespoke bileşenler (Button, Dialog, Badge...)
│       │   ├── i18n/           # TR/EN/DE/ES çeviri sözlükleri
│       │   └── stores/         # company.svelte.ts (aktif şirket)
│       └── routes/
│           ├── +layout.svelte  # Şirket switcher, dil seçici, nav
│           ├── departments/    # Departman yönetimi
│           ├── personnel/      # Personel + ajan listesi
│           ├── org-chart/      # Görsel org şeması
│           └── settings/       # AI sağlayıcılar + Git
│
├── packages/cli/               # `3pa` CLI sihirbazı (TypeScript)
├── data/                       # SQLite DB + Git repo önbelleği
└── docker-compose.yml
```

### Veri Modeli

```
Company ──< Department ──< Personnel ──── AgentConfig ──< Skill
                    │                           │
                    └── (company_id FK)         └── (responsible_id → Personnel)
```

---

## API Referansı

Sunucu çalışırken tam dokümantasyon:

- Swagger UI → `http://localhost:8000/docs`
- ReDoc → `http://localhost:8000/redoc`

### Temel Endpoint'ler

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/companies` | Şirket listesi + istatistikler |
| POST | `/companies` | Yeni şirket |
| GET | `/departments?company_id=` | Departman listesi (şirkete göre filtreli) |
| GET | `/personnel?company_id=` | Personel listesi (şirkete göre filtreli) |
| GET | `/org-tree?company_id=` | Hiyerarşik ağaç |
| GET | `/providers/status` | AI sağlayıcı durumları |
| POST | `/providers/{p}/key` | API anahtarı kaydet |
| POST | `/providers/{p}/test` | API anahtarını test et |
| GET | `/git/config` | Git bağlantı ayarları |
| POST | `/git/pull` | Repo'dan çek |
| POST | `/git/push` | Repo'ya gönder |

---

## Ortam Değişkenleri

`.env.example` dosyasını kopyalayarak başlayın:

```bash
# AI Sağlayıcılar (opsiyonel — Ayarlar sayfasından da eklenebilir)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
MISTRAL_API_KEY=...

# Frontend
VITE_API_URL=http://localhost:8000
```

---

## Geliştirme

```bash
# Backend tip kontrolü (opsiyonel)
cd backend && mypy .

# Frontend tip kontrolü
cd frontend && npm run check

# Sadece frontend build
cd frontend && npm run build
```

---

## Lisans

MIT — Ticari kullanım, fork ve katkı serbesttir.
