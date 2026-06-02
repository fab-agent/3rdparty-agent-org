# Geliştirme Notları
_Kuntay & Claude — Haziran 2026_

---

## Ne inşa ettik?

**fab.engineering** — şirketlerin AI ajanlarını, otonom süreçlerini ve değişiklik akışlarını yönettiği self-hosted bir platform. Fikir şu: bir şirketteki her "ajan personel" bir departmana bağlı, bir sorumlu insanı var, skill'leri ve policy'leri tanımlı. Bunların üzerine zamanlı görevler (flows), onay mekanizmaları (change requests) ve bir inbox bindiriyorsun — ortaya çalışan bir agentic org yönetim sistemi çıkıyor.

---

## Tech Stack ve Gerekçeler

### Backend: FastAPI + SQLModel + SQLite

**Neden FastAPI?**
Async desteği, otomatik OpenAPI dökümantasyonu ve tip güvenliği iyi bir kombinasyon. Pydantic ile gelen validasyon katmanı sayesinde schema hatalarını erken yakalıyorsun. uvicorn ile production-ready servis çok az konfigürasyonla ayağa kalkıyor.

**Neden SQLModel?**
SQLAlchemy'nin gücünü Pydantic'in tip sistemiyle birleştiriyor. Tek model tanımı hem ORM hem API schema olarak çalışıyor — DRY prensibi. SQLite ile birlikte migration overhead'i sıfır: `SQLModel.metadata.create_all()` startup'ta çalışıyor, yeni kolonlar ALTER TABLE ile ekleniyor.

**Neden SQLite?**
Tek sunucu, self-hosted senaryo için overkill olmayan seçim. Backup basit (tek dosya), deploy basit (dependency yok). Eğer ileride scale gerekirse PostgreSQL'e geçiş SQLModel üzerinden görece kolay.

**Neden monolitik `main.py` değil de modüler `api/` yapısı?**
Başlangıçta tek dosyaydı. F8 ile birlikte change_requests, flows, inbox, task_requests gibi 4 yeni router eklenince monoliti böldük. Her domain kendi `api/` modülünde — test ve okuma kolaylaşıyor, çakışma riski azalıyor.

---

### Frontend: SvelteKit 5 + Tailwind

**Neden SvelteKit?**
React/Next.js kadar kalabalık değil, compiler-based yaklaşımı sayesinde bundle küçük. Runes sistemi (`$state`, `$derived`, `$effect`) Vue Composition API'ye yakın ama daha az boilerplate. Self-hosted senaryo için SSR + SPA hybrid iyi çalışıyor.

**Neden custom UI components, shadcn-svelte değil?**
shadcn-svelte bağımlılıkları (bits-ui, melt-ui) o dönemde Svelte 5 ile tam uyumsuzdu. Button, Badge, Input gibi temel componentleri kendimiz yazdık — 50-100 satır, tam kontrol. Aesthetic shadcn/ui'dan alındı ama implementation bize ait.

**Neden Tailwind?**
Rapid prototyping için ideal. Design token sistemi (`hsl(var(--primary))` gibi) dark mode'u ücretsiz getiriyor. Utility-first yaklaşım component başına CSS yazmak yerine inline composition yapmanı sağlıyor.

---

### Scheduling: APScheduler

**Neden APScheduler?**
Celery + Redis gibi ayrı bir servis kurmak yerine process-içi scheduler. Cron syntax'ını doğrudan `CronTrigger` ile parse ediyor. SQLite'ın tek-process limitine uygun — birden fazla worker yok. Ileride Celery'ye geçiş gerekirse flow runner fonksiyonu aynı kalır, sadece tetikleyici değişir.

---

### GitHub Entegrasyonu: PyGithub (Contents API)

**Neden local git clone değil?**
Sunucuda geçici repo klonlamak disk, process ve auth yönetimi demek. GitHub Contents API üzerinden dosya oluşturma/güncelleme tek bir HTTP çağrısı. PyGithub bu çağrıyı sarmallıyor, SHA yönetimini (create vs update) otomatik hallediyor.

**Neden PAT, OAuth değil?**
MVP için PAT yeterli ve basit. Kullanıcı GitHub'da bir token üretiyor, settings'e yapıştırıyor, bitiyor. OAuth flow için callback URL, secrets yönetimi gibi ekstra altyapı gerekir — bunu erteledik.

---

## Önemli Mimari Kararlar

### Change Request: İki Aşamalı Onay

Başta "founder onayı" düşünülmüştü ama mantıklı değil — kurucunun her config değişikliğini onaylaması skalanamaz. Karar: `dept_head → admin` zinciri. Departman müdürü değişikliği teknik olarak onaylıyor, admin (sistemi kuran kişi) son kararı verip GitHub'a commit atıyor. Bu, şirkette ajan yapılandırmalarının governance'ını sağlıyor.

### Task Routing: Parent Chain Walk

Görev talebi geldiğinde sistem önce aynı departmanda skill eşleşmesi arıyor. Bulamazsa `parent_id` zincirini yukarı doğru tırmanıyor. Bu, büyük şirketlerde merkezi bir "genel ajan havuzu" yerine organik bir routing sağlıyor — her departman kendi ajanlarıyla çalışıyor, gerekirse üst birime yükseliyor.

### Flow Runner: Single API Call (Faz 1)

Şu an flow çalıştığında ajan'a tek bir LLM çağrısı yapılıyor — system prompt + task prompt, cevap inbox'a düşüyor. Tool use, multi-step reasoning, MCP bağlantısı yok. Bilinçli karar: altyapıyı önce kur, complexity sonra ekle. `flow_runner.py` izole bir servis, ilerletmek için sadece bu dosyayı değiştirmek yeterli.

### Inbox: Unified Notification Layer

Flow sonuçları, task bildirimleri, sistem mesajları hepsi aynı `InboxMessage` tablosuna düşüyor. `source_type` alanı ayırt ediyor (`flow`, `task_request`, `task_result`, `system`). Bu tasarım sayesinde ileride yeni bir event tipi eklersen (örn. CI/CD tetikleyicisi) inbox kodu değişmiyor, sadece `source_type` enum'ı genişliyor.

---

## Şu An Eksik / Sonraki Adımlar

- **LLM tool use**: Flow runner şu an single-turn. Çok adımlı görevler için Anthropic tool use API'si eklenecek.
- **RESEND_API_KEY**: Invite e-postaları şu an console'a yazılıyor, gerçek gönderim yok.
- **JWT_SECRET**: Default değer. Production'a çıkmadan önce rotate edilmeli.
- **OAuth / SSO**: PAT yeterli ama enterprise için SAML/OIDC ihtiyacı olacak.
- **Audit log**: Kim neyi ne zaman değiştirdi — compliance için kritik, henüz yok.
- **Agent memory**: Ajanlar şu an stateless — konuşma geçmişi, öğrenme yok.

---

_Bu not Docusaurus'taki resmi dökümantasyonun değil, ikimizin geliştirme sürecindeki karar defteri._
