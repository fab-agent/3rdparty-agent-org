# 3rdParty Agent Organization — Proje Planı

> **Oluşturulma Tarihi:** 2026-05-27  
> **Durum:** MVP Planlama Aşaması

---

## 1. Proje Özeti

**Proje Adı:** 3rdParty Agent Organization  
**Amaç:** Şirketlerin agentic süreçlerini yönetebileceği, açık kaynak, self-hosted bir platform.

Bu platform sayesinde firmalar:
- Organizasyon şemalarını görselleştirebilecek
- Personel bazlı AI ajanlar tanımlayabilecek
- İş tanımları, policy'ler ve skill'leri MD dosyaları üzerinden yönetebilecek
- Katkı takibi yapabilecek

---

## 2. MVP Kapsamı (Kullanıcı Onaylı)

### Mutlaka Olması Gerekenler (MVP)

- Shadcn/ui tarzı modern, basit web arayüzü
- Organizasyon oluşturma + personel ekleme
- `company.md` dosyası (vizyon, misyon, değerler + sürekli güncellenen goal)
- Her personel için `agent.md` ve `policy.md`
- Organizasyon şeması görseli (ağaç yapısı)
- Dosyaların görünür ve düzenlenebilir olması (arka plan çalışmasa bile)

---

## 3. Claude Code CLI vs Hermes Karşılaştırması

| Konu                              | Claude Code CLI                          | Hermes (Ben)                              | Karar     |
|-----------------------------------|------------------------------------------|-------------------------------------------|-----------|
| Klasör yapısı & Mimari            | Çok detaylı ve iyi yazılmış              | Daha sade ve uygulanabilir hale getirildi | Birleştirildi |
| Tech Stack                        | SvelteKit + FastAPI önerisi              | Aynı stack korundu                        | Aynı      |
| MVP Özellik Sıralaması            | Çok iyi önceliklendirme                  | P0-P1-P2 olarak sadeleştirildi            | Birleştirildi |
| UI Ekranları                      | Detaylı ekran haritası                   | Daha gerçekçi MVP ekranları önerildi      | Birleştirildi |
| MD Dosya Formatları               | Çok iyi örnekler                         | Aynı format korundu                       | Aynı      |
| Roadmap                           | 4 faza bölünmüş                          | 3 faza indirgendi (daha gerçekçi)         | Sadeleştirildi |

**Sonuç:** Claude'un planı oldukça kaliteliydi. Ben sadece şu noktalarda sadeleştirme ve gerçekçilik ekledim:
- Faz sayısını 4'ten 3'e indirdim.
- UI tarafında daha minimal bir başlangıç önerdim.
- Self-hosted ve dosya sistemi odaklı yaklaşımı güçlendirdim.

---

## 4. Önerilen Klasör Yapısı (Sadeleştirilmiş)

```
3rdparty-agent-org/
├── README.md
├── LICENSE
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── main.py
│   ├── pyproject.toml
│   ├── core/
│   │   ├── models.py
│   │   ├── file_manager.py
│   │   └── database.py
│   └── api/
│       └── routes/
│
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   └── ui/          # shadcn-svelte
│   │   └── routes/
│   └── package.json
│
├── data/
│   └── organizations/
│       └── {org-slug}/
│           ├── company.md
│           └── personnel/
│               └── {person-slug}/
│                   ├── agent.md
│                   └── policy.md
│
└── docs/
    └── plan.md
```

---

## 5. MVP Roadmap (3 Faz)

### Faz 0 — İskelet (1-2 gün)
- Docker Compose ile tek komut kurulum
- FastAPI + SvelteKit boilerplate
- Temel layout + sidebar

### Faz 1 — Temel CRUD (3-4 gün)
- Organizasyon ve personel oluşturma
- `company.md` görüntüleme + düzenleme
- Personel listesi ve detay sayfası

### Faz 2 — Agent + Policy + Şema (4-5 gün)
- `agent.md` ve `policy.md` editörü
- Organizasyon şeması (basit ağaç)
- Agent durumu (Active / Draft / Inactive)

---

## 6. Sonraki Adımlar

1. Bu planı üzerinden geçelim.
2. Onayladıktan sonra **Faz 0**'ı başlatacağız.
3. İstersen önce basit bir HTML prototype hazırlayayım (shadcn tarzı).

---

**Not:** Bu plan, Claude Code CLI'nin çıktısı temel alınarak Hermes tarafından sadeleştirilmiş ve gerçekçi hale getirilmiştir.