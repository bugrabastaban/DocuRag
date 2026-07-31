# DocuRAG — Çok Kullanıcılı Döküman Zekası Platformu

Her kullanıcının kendi hesabıyla giriş yapıp kendi dökümanlarını yüklediği ve AI destekli bir sohbet arayüzü üzerinden bu dökümanlara soru sorabildiği, production odaklı bir Retrieval-Augmented Generation (RAG) sistemi. Amaç, tekil/stateless bir demo değil; çok kiracılı (multi-tenant) veri izolasyonu, kalıcı state yönetimi ve uçtan uca bir AI pipeline'ı olan tam kapsamlı bir sistem göstermek.

**Canlı Demo:** [docu-rag-kappa.vercel.app](https://docu-rag-kappa.vercel.app)

> Not: Backend, Render'ın ücretsiz katmanında barındırılıyor; bir süre hareketsiz kaldıktan sonra ilk istek 30-50 saniye sürebilir.

---

## Ne Yapıyor

Kullanıcılar kendi hesaplarıyla kayıt olup giriş yapıyor. Her kullanıcı PDF döküman yüklüyor; bu dökümanlar parçalara (chunk) bölünüyor, embedding'e çevriliyor ve bir vektör veritabanında saklanıyor. Kullanıcı bir soru sorduğunda, sistem yalnızca *o kullanıcının kendi dökümanları* arasından anlamca en alakalı parçaları buluyor, bunları context olarak LLM'e veriyor ve context'e dayanan bir cevap üretiyor — ayrıca kullanılan kaynakları ve benzerlik skorlarını da gösteriyor, böylece cevabın arkasındaki mantık kara kutu değil şeffaf.

Sohbet geçmişi, kullanıcı bazında oturumlar arası kalıcı.

---

## Öne Çıkan Teknik Kararlar

- **Tenant izolasyonu için Row Level Security (RLS).** Veri izolasyonu yalnızca uygulama seviyesindeki `WHERE user_id = ?` filtrelerine bırakılmıyor, veritabanı seviyesinde PostgreSQL RLS politikalarıyla garanti altına alınıyor. Uygulama katmanındaki bir filtre unutulsa bile, bir kullanıcı başka bir kullanıcının satırlarına erişemiyor.
- **Ayrı bir vektör veritabanı yerine pgvector.** Döküman metadata'sı, chunk'lar, embedding'ler ve chat geçmişi doğası gereği ilişkisel (kullanıcı ve dökümana bağlı) olduğu için, vektörleri aynı PostgreSQL instance'ında (`pgvector` + HNSW index ile) tutmak, ayrı bir vektör veritabanı çalıştırıp senkronize etmenin operasyonel yükünden kaçınıyor; bu ölçekte milisaniyeler seviyesinde benzerlik araması sağlıyor.
- **JWT tabanlı auth middleware.** Kimlik doğrulama, auth kontrolünü frontend'e bırakmak yerine, her korumalı route'ta Supabase tarafından üretilen JWT'leri doğrulayan bir FastAPI dependency olarak implemente edildi.
- **Anti-halüsinasyon grounding.** Üretim (generation) prompt'u, modele yalnızca getirilen context'ten cevap vermesini ve cevap yüklenen dökümanlarda yoksa bunu açıkça belirtmesini söylüyor — tahmin yürütmüyor.

---

## Teknoloji Yığını

**Backend**
- FastAPI (Python)
- Supabase (PostgreSQL + Auth + pgvector)
- Google Gemini API (embedding + üretim)
- Docker

**Frontend**
- Vanilla JavaScript
- Tailwind CSS

**Altyapı**
- Backend, Render üzerinde (Docker runtime) deploy edildi
- Frontend, Vercel üzerinde deploy edildi
- Veritabanı, Auth ve vektör depolama Supabase'de (managed PostgreSQL)

---

## Mimari

```
Tarayıcı (JS/Tailwind)
   │  fetch + JWT bearer token
   ▼
FastAPI (Render üzerinde Docker container)
   ├── Auth middleware   → JWT'yi Supabase'e karşı doğrular
   ├── Döküman pipeline'ı → PDF → chunk → Gemini embedding → pgvector
   └── RAG pipeline'ı     → soru embedding → benzerlik araması (RLS ile sınırlı)
                              → Gemini üretim → kaynaklı, grounded cevap
   │
   ▼
Supabase (PostgreSQL + pgvector + Auth)
   ├── documents         (kullanıcı bazlı, RLS korumalı)
   ├── document_chunks    (embedding'ler, HNSW index, RLS korumalı)
   └── chat_history        (kullanıcı bazlı kalıcı, RLS korumalı)
```

---

## Temel Özellikler

- Kullanıcı bazlı veri izolasyonu ile email/şifre kimlik doğrulama
- Otomatik chunk'lama ve embedding ile PDF yükleme
- Yalnızca giriş yapan kullanıcının kendi dökümanlarıyla sınırlı semantik arama
- Kaynak gösterimli, grounded cevaplar üreten sohbet arayüzü
- Oturumlar arası kalıcı sohbet geçmişi
- Managed bir cloud veritabanından bağımsız olarak deploy edilmiş, containerize backend

---

## Veritabanı Şeması (özet)

| Tablo | Amaç |
|---|---|
| `documents` | Yüklenen her dosya için bir satır, bir `user_id`'ye ait |
| `document_chunks` | Metin parçaları + 768 boyutlu embedding'ler, benzerlik araması için HNSW indeksli |
| `chat_history` | Kullanıcı ve (opsiyonel olarak) döküman bazında soru/cevap çiftleri |

Üç tabloda da Row Level Security aktif, politikalar erişimi `auth.uid() = user_id` ile sınırlıyor.

---

## Yerelde Çalıştırma

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Ya da Docker ile
docker build -t docurag-backend ./backend
docker run -p 8000:8000 --env-file .env docurag-backend
```

Gerekli ortam değişkenleri (`.env`):
```
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
GEMINI_API_KEY=
```

Frontend statik — `frontend/index.html`'i doğrudan açabilir ya da herhangi bir statik dosya sunucusuyla servis edip `config.js`'i kendi backend adresine yönlendirebilirsin.

---

## Geliştiren

Buğra — AI Engineer, production-grade AI sistemlerine odaklı.
