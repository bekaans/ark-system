# ARK Intelligence — Sistem Özeti

Bu repo, **Ark Intelligence** adlı ajans/satış-otomasyon projesinin teknik altyapısını içerir.
Bir Claude Code oturumu bu repoyu (ve git log'unu) okuyarak projenin tam bağlamını yeniden kurabilir.

## İş modeli (özet)

Yerel işletmelerin dijital eksikliğini (site yok/kötü site) tespit edip, otomatik olarak
(1) lead bul, (2) nitelendir, (3) animasyonlu vitrin sitesi üret, (4) sat — döngüsünü
mümkün olduğunca insansız yürüten bir sistem. Orijinal 40 maddelik yol haritası
`~/Desktop/ark-kontrol-listesi.pdf` (detaylı, ajan kartları + skill atamaları dahil;
`~/Downloads/ark-kontrol-listesi.html` daha kısa bir önceki sürüm) — S0: marka/altyapı,
S1: lead makinesi, S2: şablon/vitrin, S3: bot/reklam/CRM, S4: tam otomasyon.

**Ürün hattı (2026-07-19 itibariyla güncel — eski "3D"/"7D" isimleri TERK EDİLDİ):**
dm-qualifier persona skill'inde belgelendi (`.agents/skills/turkce-nlp-satis-hitabet/SKILL.md`
→ "Hizmetlerimiz"). 4 kademeli yapı, HER kademede müşterinin KENDİ fotoğrafı kullanılır
(jenerik/stok içerik yok) — fark sadece o fotoğrafa ne kadar animasyon uygulandığında:
- **B (10-15bin TL)** — Kling videosu YOK, müşteri fotoğrafı düz/statik + CSS Ken Burns.
- **A (15-20bin TL)** — müşteri fotoğrafından KISA bir Kling image-to-video giriş efekti.
- **S (20-25bin TL)** — müşteri fotoğraflarından TAM Kling image-to-video hero, scroll-scrub.
- **S+ (25-45bin TL)** — S'in üstüne hover'da canlanan hizmet kartları + `pinned_story`
  katalog bölümü + tüm geçiş efektleri (WebGL/Three.js YOK, hepsi GSAP+Canvas2D).
- **SEO 2.0** — düz/generik SEO değil; sektöre ve bölgeye özel arama sorgularında
  (ör. "[şehir] oto galerisi") müşterinin sitesini reklama para vermeden organik
  olarak üst sıralara taşıyan ayrı bir hizmet. Bağımsız istenirse aylık 5.000 TL,
  Ark Intelligence'in kendi web sitesi (B/A/S/S+) müşterilerine aylık sabit 2.500 TL
  (bundle indirimi). dm-qualifier'da kaçamak-cevap durumunda 1 aylık sınırlı-süreli
  hediye olarak da kullanılıyor (gerçek değeri 2.500 TL, website müşterisi için).
  Ayrıca site teslim edilip müşteri memnuniyeti teyit edildikten SONRA (kesinlikle
  öncesinde değil) SEO 2.0 almamış müşterilere çapraz-satış olarak da sunuluyor
  (SKILL.md → "Teslim-Sonrası SEO 2.0 Çapraz-Satış").

Bu yapı S2 (şablon/vitrin) ve madde 34 (fiyat kademeleri) için referans alınmalı.
`leads.estimated_deal_value` artık `leads.tier` (eski_sistem/ortalama/iyi — 2026-07-19'da
A/B/C'den yeniden adlandırıldı) bazında `score_leads.py`'deki `DEFAULT_DEAL_VALUE` ile
bağlanmış durumda (kaba/beklenen değer — hangi müşterinin hangi website tier'ini
seçeceği konuşma sırasında belli olur, kesin ürün eşlemesi henüz otomatik değil).

**Önemli:** PDF'teki tam plan bu repodaki mimariden daha geniş — ayrıca **Cortex** (GPT
çapraz-model kod denetçisi), ayrı **Frontend/Backend İnşaatçı** Claude Code rolleri,
**mission-control** (Bexi/Yönetici için önerilen hazır araç) ve **mem0** (uzun vadeli org
hafızası) tanımlıyor. Bunlar henüz bu repoda yok, S0 bitince sırayla ele alınacak.

## Ajan mimarisi

| Ajan | Görev | Neden bu tasarım |
|---|---|---|
| **Ajan 1** | NACE taksonomi filtreleme, sektör/lead skorlama (yüksek hacim) | Cerebras'ın günlük 14.400 istek ücretsiz kotası hacme uygun |
| **dm-qualifier** | Türkçe WhatsApp/Instagram DM nitelendirme botu | Groq'un düşük gecikmesi gerçek zamanlı sohbet için kritik |
| **Ajan 2** | Referans videodan Higgsfield/AI video prompt'u çıkarma (multimodal) | Gemini native video anlamada rakiplerinden belirgin önde |
| **Ajan 3** | site-assembler: config → video → şablon → kalite kapısı → deploy orkestrasyonu | Gerçekten Claude Code üzerinden (headless) çalışan tek ajan — kod/araç kullanımı ağırlıklı |
| **Bexi** | Kullanıcıya (sana) özet/soru-cevap/komut yönlendirme asistanı | Tek arayüz, WhatsApp + web chat (PWA), ayrı ajanlarla tek tek konuşma derdi yok |

`bexi-app/` klasörü Bexi'nin sohbet arayüzü (Next.js PWA) içindir — telefonda "Ana Ekrana Ekle" ile
uygulama gibi çalışır, bilgisayardan tarayıcıdan erişilir. Henüz Supabase'e bağlanmadı (aşağıya bak).

## Model yönlendirme stratejisi

**Kısıt:** Sistem 7/24 durmadan çalışmalı, ama bütçe hedefi mümkün olduğunca $0.
**Çözüm:** Her ajan için 2 ücretsiz + gerekirse 1 ucuz-ücretli model, farklı sağlayıcılardan
(aynı sağlayıcıda birden fazla key almanın kotayı çoğaltmadığı doğrulandı — limit hesap
bazında, key bazında değil; bu yüzden gerçek yedeklilik farklı sağlayıcılar gerektiriyor).

`litellm/config.yaml` tüm zincirleri tanımlar. LiteLLM router seçildi çünkü (a) Ajan 1/2/dm-qualifier
Claude Code'un dışında çalışan bağımsız script'ler — ccr bunlar için doğru araç değil, sadece
gerçekten Claude Code üzerinden çalışan Ajan 3 için ccr kullanılıyor; (b) LiteLLM hata-tipine göre
otomatik fallback/retry/cooldown yönetiyor, elle yazmaktan daha sağlam.

**Önemli, tekrar tekrar doğrulanan gerçek:** Sağlayıcıların ücretsiz model kataloğu ve model
isimleri sık değişiyor (Qwen3 Coder 480B:free kaldırılıp geri geldi, Cerebras Llama 3.3 70B'yi
kaldırıp gpt-oss-120b/zai-glm-4.7/gemma-4-31b'ye geçti, Gemini'de gemini-3.1-flash artık yok).
`config.yaml`'daki model isimleri zaman zaman kontrol edilmeli.

### Sağlayıcı bazında durum (son test: 2026-07-15)

| Sağlayıcı | Kullanım | Kota | Durum |
|---|---|---|---|
| Cerebras (`gpt-oss-120b`) | Ajan 1 birincil | 14.400 istek/gün | ✅ test edildi |
| Groq (`llama-3.3-70b-versatile`) | dmq birincil, Bexi yedek | 1.000 istek/gün, düşük gecikme | ✅ test edildi |
| Google AI Studio (Gemini) | Yedek katman (çoğu ajan) | 1.500 istek/gün/model | ⚠️ flash-lite ✅, tam flash geçici 503 verdi (Google tarafı) |
| OpenRouter (çeşitli `:free`) | Son çare yedek | Hesap-bazlı paylaşımlı 50/gün (kredi yoksa) | ✅ Nemotron modelleri calisti, Llama 3.3 free rota gecici 429 (Venice saglayici, hesabimizla ilgisiz) |
| OpenRouter (`deepseek/deepseek-v4-pro`) | Bexi birincil | Ücretli, $0.435/$0.87 per 1M token (giriş/çıkış, 2026-07-16 canlı doğrulandı) | ✅ 2026-07-16: $5 bakiye yüklendi, test edildi (gerçek çağrı: 24 giriş + 65 çıkış token = $0.000067) |
| Anthropic (`claude-haiku-4-5-20251001`) | dmq/Bexi **son çare** fallback | Ücretli | ⏳ key eklendi ama bilinçli olarak **bakiye yüklenmedi** — sadece 3 ücretsiz katman da çökerse tetiklenir, gereksiz yere para yatırılmadı |

**Not:** Plandaki S0/6 maddesi Claude API'yi dm-qualifier ve Yönetici'nin "beyni" olarak
varsayıyordu (ücretsiz zincir değil). Karar: Anthropic key'i plana uymak için eklendi ama
maliyeti sıfırda tutmak için sadece son-çare fallback yapıldı — gerçek trafik gösterip
ihtiyaç doğarsa bakiye yüklenecek.

### dm-qualifier model zinciri — parametre sayıları (2026-07-16 doğrulandı)

| Sıra | Model | Parametre |
|---|---|---|
| 1 (birincil) | Groq `llama-3.3-70b-versatile` | **70B**, dense — Meta'nın resmi model kartında açık |
| 2 (yedek) | Gemini `gemini-flash-latest` | Google resmi olarak açıklamıyor |
| 3 (yedek) | OpenRouter `meta-llama/llama-3.3-70b-instruct:free` | **70B**, dense — Groq'takiyle aynı Llama 3.3 70B |
| 4 (son çare) | Anthropic `claude-haiku-4-5-20251001` | Anthropic resmi olarak açıklamıyor |

Google ve Anthropic, kapalı-kaynak modellerinin parametre sayısını hiçbir zaman resmi
olarak yayınlamıyor — bu bir eksik veri değil, iki firmanın da kalıcı politikası.
Sadece açık-kaynak (Meta Llama) satırları için kesin rakam var.

## Kurulum durumu

**S0 — Marka + Altyapı**
- [x] 1. Domain + marka araştırması — **arkintelligencelabs** olarak karar verildi (ilk denemede "arkintellenge" yazım hatası yapıldı, düzeltildi; ayrıca doğru yazım "arkintelligence.com" 2018'den beri başkasına ait ve 2033'e kadar kilitli olduğu için "labs" eklendi). Kayıt: turkticaret.net, uzantılar `.com` `.store` `.com.tr` `.online`, 1 yıllık, başlangıç 2026-07-16 (yenileme: 2027-07-16). Tümü müsaitlik kontrolünden geçti (whois ile doğrulandı). TÜRKPATENT marka sorgulaması kullanıcı tarafından yapıldı — "Ark Intelligence" / "Ark Intelligence Labs" için çakışan tescilli marka yok.
- [ ] 2. Logo — yapılmadı
- [ ] 3. Instagram + LinkedIn hesapları — yapılmadı
- [ ] 4. Google Workspace kurumsal mail — yapılmadı
- [x] 5. Supabase projesi + 5 tablo (sectors, businesses, audits, leads, conversations) — kuruldu, RLS aktif, `supabase/schema.sql`
- [~] 6. API anahtarları — Cerebras/Groq/Gemini/OpenRouter/Anthropic `.env`'de. Google Ads: MCC hesabı + developer token (Test seviyesi) alındı, ama **Basic Access başvurusu ertelendi** — şirket web sitesi olmadan (`madde 1` bekliyor) Google başvuruyu reddedebiliyor, ayrıca gerçek reklam harcaması olmadan sadece kaba aralık verisi (ör. "1K-10K") dönüyor. Karar: domain alınana kadar bekletiliyor; sektör puanlamasında CPC şimdilik atlanıp diğer sinyallerle (dijital gerilik oranı, işletme hacmi) ilerlenecek, CPC sonradan haftalık kalibrasyona eklenir.
- [x] 7. GitHub mono-repo `ark-system` — private repo, ama klasör yapısı plandaki `/agents /skills /template /chatbot` değil, `/litellm /bexi-app /supabase` oldu
- [x] 8. Geliştirme ortamı: Superpowers (resmi marketplace), claude-mem (thedotmack/claude-mem), find-skills (vercel-labs/skills) kuruldu — hafıza testi ("oturum kapat-aç") ancak gerçek yeni bir oturumda doğrulanabilir, henüz yapılmadı

**S0 tamamlandı sayılır** (1-4 hariç — bunlar marka/iş kararları, kullanıcı yapmalı).

**S1 — Ajan 1: Lead Makinesi** (Hafta 2-3)
- [x] 9. NACE taksonomisini yükle + filtrele — `colaberry/WorldOfTaxonomy` reposu klonlandı (`agents/WorldOfTaxonomy/`, .gitignore'da), bundled `tree-data/nace_rev2.json`'dan 360 aday sınıf okundu, Ajan 1 LLM zinciriyle (Cerebras) filtrelendi, **23 sektör** `sectors` tablosuna yazıldı (`agents/ajan1/filter_nace.py`). İlk modelin yanlış işaretlediği 6 üretim/imalat sınıfı (giyim/ayakkabı/elektronik üretimi, reklamcılık) elle çıkarıldı.
- [x] 10. Sektörleri veriyle puanla, ilk 20'yi seç — **CPC adımı ertelendi** (Google Ads Basic Access sitesiz reddedilebiliyordu + gerçek reklam harcaması olmadan sadece kaba aralık veriyor); `opportunity_score = (business_volume/100) x digital_weakness_ratio x 100` formülü kullanıldı. İşletme hacmi: `gosom/google-maps-scraper` ile 23 sektör × 5 şehir (İstanbul, Ankara, İzmir, Bursa, Antalya) = 115 sorgu, **2.195 tekil işletme**. Dijital gerilik: Playwright ile 365 site denetlendi (GSAP/animasyon + basit SEO skoru, `agents/ajan1/audit_sites.py`). Puanlama + ilk 20 işaretleme `agents/ajan1/score_sectors.py` — top 20 `sectors.weight=1.0`, kalan 3 `weight=0.0`. En yüksek puanlı: **Oto galerileri (45.1, skor 71.4)** — çok işletme + çoğunda zayıf/eski site.
- [x] 11. Toplayıcı — yukarıdaki taramayla fiilen tamamlandı, işletmeler `businesses` tablosunda (place_id ile mükerrer engellendi).
  - **Kaynak kod hatası düzeltildi (2026-07-16):** `sector_terms.py`'da "56" ve "56.1" ikisi de "restoran" terimini paylaşıyordu, bu yüzden `import_businesses.py`'daki `TERM_TO_CODE` ters-eşleme sözlüğü (son key kazanır) "56"'yı sessizce düşürüyordu — tüm işletmeler "56.1"e yazılmıştı, "56" hacimsiz kalmıştı (o zaman elle DB'de yama yapılmıştı). Artık "56" → "lokanta", "56.1" → "restoran" olarak ayrıştırıldı, 23 terim de artık benzersiz (test edildi). **Not:** bu sadece KAYNAK KODU düzeltir — mevcut DB'deki 56/56.1 verisi hâlâ eski/yamalı durumda; düzgün ayrışması için toplama+puanlama pipeline'ının (madde 10-11) "lokanta"/"restoran" için yeniden çalıştırılması gerekir, henüz yapılmadı.
- [x] 12. Site denetçisi — `agents/ajan1/audit_sites.py`, Playwright + regex tabanlı GSAP/Meta Pixel/gtag tespiti + basit SEO skoru (tam Lighthouse değil, hafif sezgisel skor). Ekran görüntüleri `agents/ajan1/data/screenshots/` (gitignore'da, ~37MB ham veri repoya girmiyor).
- [x] 13. Lead puanlama + Tier ataması — `agents/ajan1/score_leads.py`: zayıflık sinyali (sitesi yok/kötü) + büyüklük sinyali ağırlıklı `lead_score`, eşikler 80+/60-79/altı. İlk çalıştırmada rapor edilen "1.000 lead" rakamı **PostgREST 1000-satır limiti yüzünden yanlıştı** — s1-7 sırasında bulunup düzeltildi (bkz. aşağıda), **gerçek sayı 2243 lead** (832 A/1135 B/276 C). Tahmini anlaşma değeri artık gerçek fiyatlarla (s3-9: A=24k/B=18k/C=12k TL).
- [~] 14. Tier A ilk mesaj taslakları — `alirezarezvani/claude-skills@cold-email` skill'i kuruldu (`.claude/skills/cold-email`, 22.7K yıldız, onaylandı), ilkeleri (akran gibi yaz, kanıt-tabanlı kişiselleştirme, tek istek) WhatsApp DM formatına uyarlandı (`agents/ajan1/draft_outreach.py`). İlk denemede model uydurma kişi adı ("Merhaba Ahmet") ve sahte "Instagram'ınızı takip ediyorum" iddiaları üretti — prompt'a bunları yasaklayan açık kural eklenip düzeltildi. **İlk 10 taslak** üretildi, kullanıcı onayı bekliyor (checklist kuralı: ilk 10 elden geçirilir). Uygunsuz işletme sorunu için karar: `leads.status` alanına `flagged` eklendi (CHECK constraint güncellendi). `agents/ajan1/flag_inappropriate.py` anahtar kelime taramasıyla (yetişkin ürünleri, silah, kumar) otomatik işaretliyor — **4 lead flagged** (hepsi yetişkin ürünleri mağazası). `agents/ajan1/status_report.py` flagged listesini isim+sektör olarak gösteriyor (Bexi'nin ileride yapacağı raporlamanın ilk hali), `agents/ajan1/approve_leads.py` kullanıcı onayıyla `status='new'`'a geri alıyor. Kullanıcı onayı olmadan flagged lead'lere outreach gönderilmiyor. **2026-07-16 eklendi:** `status_report.py` artık raporun sonunda OpenRouter'daki kalan bakiyeyi de gösteriyor (`/api/v1/credits` endpoint'i, canlı test edildi: "$5.00 kaldi, yuklenen $5.00, harcanan $0.0004") — Bexi canlıya geçtiğinde bu da onun durum raporunun bir parçası olacak.
- [x] s1-7. Sürekli-çalışan döngü (2026-07-16, gecelik değil "açık olduğu sürece" — kullanıcı tercihi) — `.github/workflows/ajan1-loop.yml`: GitHub Actions `schedule` (`*/30 * * * *`, ayrıca `workflow_dispatch` ile elle tetiklenebilir) her çalıştığında `agents/ajan1/run_next_batch.py`'yi koşturur. Script: (1) `scrape_progress` tablosunda bekleyen (sektör,şehir) çiftlerinden bir grup (10) alır — ilk 5 şehir zaten 'done', **10 yeni şehir eklendi** (`CITIES_EXPANSION`: Adana, Gaziantep, Konya, Mersin, Kayseri, Eskişehir, Diyarbakır, Samsun, Denizli, Şanlıurfa) 'pending' olarak tohumlandı; (2) `google-maps-scraper`'ı sadece o grup için çalıştırır, `businesses`'e ekler (`sector.business_volume` üzerine yazılmaz, **artırılır**); (3) henüz denetlenmemiş birkaç siteyi denetler; (4) `score_sectors.py`+`score_leads.py`'yi (ikisi de idempotent) yeniden çalıştırır; (5) işlenen çiftleri 'done' işaretler. Hata olursa Telegram'a bildirim (bot: `BexiIntelligenceBot`, kullanıcı kendi kurdu, token+chat_id GitHub secret olarak eklendi). GitHub Actions runner'da `google-maps-scraper` kaynağından (`gosom/google-maps-scraper`, zaten onaylı) klonlanıp derleniyor — repoya binary commitlenmedi (65MB, .gitignore'da zaten).
  - **Gerçekte 4 hata bulundu, hepsi düzeltildi, GitHub Actions'ta uçtan uca doğrulandı (✓ 9m35s):**
    1. Scraper binary'si `-exit-on-inactivity` bayrağı olmadan işini bitirse bile süreçten çıkmıyordu — bayrak eklendi.
    2. **`score_leads.py` ve `flag_inappropriate.py`, PostgREST'in varsayılan 1000 satır limitine takılıyordu** — sayfalama (`.range()`) olmadan tek `.execute()` çağrısı yapıyorlardı, bu yüzden gerçekte **2243 işletme** varken (top-20 sektörde) sessizce sadece ilk 1000'i işliyorlardı. İkisi de sayfalanacak şekilde düzeltildi: **gerçek lead sayısı 1000 değil 2243** (832 A/1135 B/276 C) — önceki "1.000 lead" rakamı yanlıştı. `flag_inappropriate.py` tüm 2239 'new' lead'i yeniden taradı, yeni uygunsuz işletme çıkmadı.
    3. **playwright-go v0.6000.0 (google-maps-scraper'ın bağımlılığı), sabit "1.60.0" sürümünü ölü `playwright.azureedge.net` CDN'inden indirmeye çalışıyordu** (proje geçmişinde yerel ortamda da yaşanmış bilinen upstream hata — bu sürüm gerçekte hiçbir CDN'de yok). CI'da çözüm: npm registry'den gerçek bir sürümü (`playwright-core@1.57.0`) çekip `package.json`'daki `version` alanını "1.60.0" olarak etiketleyip playwright-go'nun beklediği cache yoluna (`~/.cache/ms-playwright-go/1.60.0`) yerleştirmek — `isUpToDateDriver()` kontrolü sadece `cli.js --version` çıktısına bakıyor, gerçek indirmeyi hiç denemiyor. `PLAYWRIGHT_NODEJS_PATH` ile sistem node'u kullanılıyor (gömülü node binary gerekmiyor).
    4. Bir (sektör,şehir) çifti onlarca işletme detay sayfası açabiliyor — 10'luk batch CI'da yavaş kalıp zaman aşımına düşüyordu. `BATCH_SIZE` 10'dan **3**'e indirildi (zaten "acele değil, sürekli" felsefesine daha uygun), subprocess timeout 600→900sn, job timeout-minutes 15→25.
- [ ] s1-8. İlk Tier A mesajlarını gönder [GATE: OUTBOUND] — WhatsApp/Chatwoot (s3-1/2/3) tamamlanmadan mümkün değil.

**Not:** Bu adımlar şu an **ben (Claude Code) tarafından elle çalıştırılıyor** — Ajan 1 henüz bağımsız/otomatik çalışmıyor. Madde 15'te (adı değişecek: "sürekli döngü") bu script'ler bir servise bağlanınca gerçek anlamda "Ajan 1 çalışıyor" denebilecek.

**S2 — Şablon + Vitrin** (Hafta 4-5) — *madde ID'leri artık orijinal checklist'teki gibi (`s2-1` vb.), çünkü PDF kayboldu ama `~/Downloads/ark-kontrol-listesi.html` ikizi bulunup tam 40 madde doğrulandı.*
- [x] s2-2. site.config.json şemasını dondur — `template/site.config.schema.json` (JSON Schema draft 2020-12), `template/site.config.example.json` (dolu örnek, oto galeri), `template/validate_config.py` (harici bağımlılıksız mini validator — eksik/boş zorunlu alan + geçersiz `tier`/`deploy.status` + 7D için boş `media.customer_photos` kontrolü). Hem geçerli hem bilerek bozulmuş bir config ile test edildi, ikisi de doğru sonuç verdi.
- [~] s2-1. Şablon v1 motorunu yaz (2026-07-18) — `template/app/`: Vite + vanilla TS + GSAP ScrollTrigger. `src/canvas-frame-sequence.ts`: scroll pozisyonunu (0-1) kare indeksine eşleyip canvas'a çizen komponent (Apple ürün sayfası tarzı scroll-scrubbing), gerçek Higgsfield kareleri henüz yokken (s2-3/s2-6) 404 alırsa otomatik renkli placeholder'a düşüyor — bu sayede scroll-scrubbing mantığı gerçek görsel olmadan da test edilebildi. `src/sections.ts`: 5 bölüm (hero, services_grid, animation_2, social_proof, contact) `site.config.json`'dan okunup render ediliyor. Tarayıcıda gerçek test edildi: config'ten başlık/headline doğru geldi, scroll ile kare rengi değişti (frame mapping çalışıyor), hero pinlendi (GSAP pin+scrub doğrulandı), tüm 5 bölüm sırayla render oldu. **Eksik:** Gerçek cihaz testi (iPhone + ucuz Android) — bu ortamda fiziksel cihaz/emülatör erişimi yok, kullanıcı kendisi test etmeli (CSS zaten `clamp()`/`vw`/grid `auto-fit` ile responsive yazıldı).
- [x] s2-4. ui-ux-pro-max + impeccable kurulumu (2026-07-18) — `nextlevelbuilder/ui-ux-pro-max-skill@ui-ux-pro-max` ve `pbakaus/impeccable@impeccable` kuruldu (`.agents/skills/`). `template/app/`'da `impeccable init` akışı çalıştırıldı: **PRODUCT.md** (register=brand, kullanıcılar=yerel işletme müşterileri+ARK ekibi, pozisyon="sektöre özel scroll-animasyonlu vitrin") ve **DESIGN.md** (North Star: "The Sector Mirror" — sablon kendi kimliğini dayatmaz, sektöre göre renk/karakter değiştirir; bileşen felsefesi: "dokunsal ve enerjik") gerçek `style.css` token'ları taranarak (scan mode) yazıldı, `.impeccable/design.json` sidecar'ı da üretildi. **Kod dokümantasyonla senkron tutuldu:** kart/buton hover state'leri (`translateY(-4px)`, `scale(1.04)`, ease-out-quart) ve `prefers-reduced-motion` desteği (canvas pinlemesi yerine statik orta kare) DESIGN.md'nin kendi "Do's and Don'ts" listesine göre gerçek CSS/TS'e eklendi, tip kontrolü geçti.
- [x] s2-3. Higgsfield MCP bağla + video model testi (2026-07-18) — **yön değiştirdi ve kapatıldı.** Kapsamlı canlı tarayıcı araştırması (10 gerçek site incelendi, `.agents/skills/kling-video-prompt/references/`) sonunda: (1) Higgsfield'ın Kling 3.0'ı ~$0.45/video'ya sattığı, doğrudan Kling.ai üzerinden aynı modelin ~$0.15/video olduğu doğrulandı (aracı marjı) — ama Higgsfield'ın gerçek katma değeri (Cinema Studio kamera preset'leri, Mr. Higgs otomatik yönetmen, çoklu-model tek abonelik) de araştırılıp not edildi; (2) `.agents/skills/kling-video-prompt/SKILL.md` yazıldı — Kling 3.0 için 5 parçalı prompt yapısı (Subject/Motion/Camera/Scene/Style) + 7D'nin özü olan "gerçek müşteri fotoğrafını image-to-video ile canlandırma" iş akışı ("Subject + Movement" formülü, negative prompt listesi); (3) `agents/ajan3/kling_to_frames.py` planlandı (Kling klibini `frame-0001.jpg...` formatına çeviren ffmpeg pipeline'ı, mevcut `canvas-frame-sequence.ts` hiç değişmeden okuyabiliyor). **Higgsfield'a hiç bağlanılmadı, MCP kurulmadı** — doğrudan Kling.ai kullanılacak.
- [ ] s2-5, s2-6, s2-7, s2-8, s2-9 — henüz başlanmadı (sırasıyla: 21st.dev, 2×3 örnek vitrin, kalite kapısı, reels, canlıya alma). s2-6 için sektör kararı: Gıda/İçecek perakendesi (opportunity_score 254.5) + Otomotiv (251.3) — Ajan 1'in en yüksek skorlu 2 sektörü.

**S+ (Three.js/WebGL) tier — kasıtlı olarak ERTELENDİ:** Aynı araştırmada (robinpayot.com, ujjwalagarwal.com, lejardin.pha5e.com, exp-gemini.lusion.co, marseille.laphase5.com gibi bespoke Three.js/WebGL siteler) incelenen her örnek ya yavaştı (10-25sn yükleme) ya da tamamen bozuktu (marseille.laphase5.com 3 denemede hiç açılmadı) — bu, `template/app/PRODUCT.md`'nin "Lighthouse mobil ≥85, görsel efekt performanstan asla çalmaz" taviz verilemez ilkesiyle doğrudan çelişiyor. robinpayot.com'un kendi yaratıcısına 8 ay sürmesi de bunun config-tabanlı/otomatik-monte-edilen bir ürün "tier"ı değil, proje-bazlı özel mühendislik olduğunu gösteriyor. Karar: `site.config.schema.json`'a yeni bir tier eklenmedi, Ajan 3'e bağlanmadı. Gerçek bir müşteri talebi gelirse ayrı/config-dışı özel proje olarak ele alınacak. Bunun yerine, aynı araştırmadan çıkan **katalog/portföy deseni** (otsuka-air.jp — pin + dönen fotoğraf + ilerleme-pill) `sections.pinned_story` adında opsiyonel bir bölüm olarak mevcut motora eklendi (2026-07-18) — **Lenis eklenmedi**, mevcut `canvas-frame-sequence.ts` ile AYNI GSAP ScrollTrigger pin+scrub mekanizması (`template/app/src/pinned-story-section.ts`) yeterli oldu, tarayıcıda scroll test edildi (pin/crossfade/pill/reduced-motion fallback çalışıyor). `agents/ajan3/kling_to_frames.py` de yazıldı (Kling klibini `frame-0001.jpg...` kare dizisine çeviren ffmpeg pipeline'ı, sentetik klip ile uçtan uca test edildi).

**TIER YENİDEN ADLANDIRMA (2026-07-19) — "3D"/"7D" isimleri TERK EDİLDİ, yeni 4 kademeli B/A/S/S+ yapısı:** Kullanıcı activetheory.net'i referans verdi (canlı incelendi: gerçek Three.js/WebGL2 motoru, 1.75MB JS bundle, yükleme testinde 30+ saniye `/75`'te takılı kaldı — yukarıdaki S+/WebGL reddinin gerekçesiyle birebir aynı risk). Bu vesileyle tüm fiyat/tier yapısı yeniden kuruldu. **Kritik ilke değişikliği: artık HER tier müşterinin KENDİ fotoğraflarını kullanır** — eski "3D = jenerik/stok içerik, müşteri fotoğrafı gerekmez" kuralı KALKTI. Fark artık sadece o fotoğraflara ne kadar animasyon/efekt uygulandığında:

| Yeni tier | Eski karşılığı | Fiyat | Ne yapılır |
|---|---|---|---|
| **B** | (yeni, yok) | 10.000-15.000 TL | Kling videosu YOK. Müşteri fotoğrafı düz/statik konur + CSS Ken Burns (yavaş zoom) + fade-in. |
| **A** | eski "3D" | 15.000-20.000 TL | Müşteri fotoğrafından KISA bir Kling image-to-video giriş efekti. |
| **S** | eski "7D" | 20.000-25.000 TL | Müşteri fotoğraflarından TAM Kling image-to-video hero, scroll-scrub animasyon. |
| **S+** | eski "S" (bir önceki paragraf) | 25.000-45.000 TL | S'in üstüne: hover'da canlanan hizmet kartları (`photo`/`hover_clip`) + `pinned_story` katalog bölümü + tüm geçiş efektleri — ARK'ın kendi sitesine benzer, kişiselleştirilmiş. WebGL/Three.js YOK, hepsi GSAP+Canvas2D. |

Yapılan değişiklikler:
- `site.config.schema.json`: `tier` enum'u `["B","A","S","S+"]`. `sections.hero`'da `video_asset`/`frame_count` artık opsiyonel, yeni `image` alanı (B tier); `sections.animation_2` tamamen opsiyonel (B tier'de yok, `sections.required` listesinden çıkarıldı).
- `validate_config.py`: `VALID_TIER` güncellendi. Tier-koşullu kurallar: B→`hero.image` zorunlu; A/S/S+→`hero.video_asset`+`frame_count`+`animation_2` zorunlu; **HER tier→`media.customer_photos` zorunlu** (artık jenerik içerik yok); S+→ayrıca `pinned_story` zorunlu. 6 senaryo (geçerli+bozuk × B/A/S+) ile test edildi, hepsi doğru sonuç verdi.
- `template/app/src/config.ts`, `sections.ts`: `renderHero` artık `hero.video_asset` varsa kare-dizisi, yoksa `hero.image` ile statik CSS-animasyonlu hero render ediyor; `renderAnimation2` opsiyonel (yoksa atlanıyor). Tarayıcıda B tier hero'su uçtan uca test edildi (statik görsel + Ken Burns doğru render oldu, console hatasız).
- `showcases/*/site.config.json` (6 dosya) + `template/site.config.example.json`: tier `"3D"`→`"A"`, hepsine placeholder `media.customer_photos` eklendi.
- `.agents/skills/turkce-nlp-satis-hitabet/SKILL.md`: Hizmetlerimiz bölümü B/A/S/S+ olarak yeniden yazıldı.
- ARK'ın kendi kurumsal sitesi S+ pipeline'ını kullanacak (bkz. `.agents/skills/kling-video-prompt/references/ark-kurumsal-hero-taslak.md`) — Kling bakiyesi yüklenince üretime geçilecek.

**LEAD/SATIŞ TIER İSİMLERİ DE DEĞİŞTİ (2026-07-19) — isim çakışması tamamen çözüldü:** Website ürün tier'i (B/A/S/S+) ile çakışan `leads.tier` (A/B/C) ve `leads.sales_tier` (S/A/B/C/D) harf sistemleri de tanımlayıcı Türkçe isimlere geçirildi:

| Eksen | Eski | Yeni |
|---|---|---|
| `leads.tier` (ön-satış lead kalitesi, `score_leads.py`) | A / B / C | **eski_sistem** / **ortalama** / **iyi** (müşterinin MEVCUT sitesinin durumunu tanımlar — "eski_sistem" = en yüksek fırsat) |
| `leads.sales_tier` (sohbet-içi kapanış yakınlığı, `score_conversations.py`) | D / C / B / A / S | **sadece_merak** / **kararsız** / **soğuk_satış** / **potansiyel_olabilir** / **potansiyel_müşteri** |

**Ayrıca `score_conversations.py`'nin sınıflandırma mantığı GEREKLİLİK-TABANLI bir algoritmaya çevrildi** (kullanıcının "hangi seviyede olduğunu öğrenip bir üste taşımak" tarifine göre): `potansiyel_musteri` olmak için 3 bağımsız gereklilik aranıyor — `sistemi_biliyor` (sistemi anladı mı), `istiyor` (açık istek ifadesi var mı), `ariyor_sorunu_var` (somut bir ihtiyaç/sorun tanımladı mı). Müşteri randevu/fiyat istedi ama bu 3'ü tam sağlamadıysa (`potansiyel_olabilir`), eksik olan gerekliliği hedefleyen somut bir aksiyon üretiliyor (sistemi öğret / isteği netleştir / sorunu ortaya çıkar) — tek bir "ilk eşleşen kazanır" regex'i değil, bağımsız sinyal kombinasyonu. `agents/ajan2/test_score_conversations.py` (yeni dosya) 9 senaryoyla (boş mesaj, soğuk, itiraz, eksik-gereklilikli randevu, tam-gereklilikli randevu, doğrudan kapanış vb.) test edildi, hepsi geçti.

Değişen dosyalar: `supabase/schema.sql` (CHECK kısıtları), `supabase/migrations/008_tier_isim_degisikligi.sql` (yeni migration — eski verideki A/B/C ve S/A/B/C/D değerlerini yeni isimlere çevirir, **SQL Editor'a elle yapıştırılması gerekiyor**), `agents/ajan1/score_leads.py`, `agents/ajan1/draft_outreach.py`, `agents/ajan1/status_report.py`, `agents/ajan2/score_conversations.py` (+ yeni test dosyası), `agents/bexi-telegram/hourly_digest.py`, `agents/bexi-telegram/bridge.py` (legacy/kullanılmıyor ama tutarlılık için düzeltildi), `.agents/skills/turkce-nlp-satis-hitabet/SKILL.md` (Sohbet-içi Satış Tier'i bölümü gereklilik-tabanlı modele göre yeniden yazıldı).

**✅ İsim çakışması ÇÖZÜLDÜ (aynı gün, yukarıdaki paragrafta detaylı):** İlk fark edildiğinde `leads.tier` (eskiden A/B/C) ve `leads.sales_tier` (eskiden S/A/B/C/D) bu WEBSİTE ÜRÜN tier'i (B/A/S/S+) ile AYNI HARFLERİ kullanıyordu. Artık ikisi de tanımlayıcı Türkçe isimlere (eski_sistem/ortalama/iyi ve sadece_merak/kararsız/soğuk_satış/potansiyel_olabilir/potansiyel_müşteri) geçirildiği için çakışma kalmadı — tek harf-tier B/A/S/S+ artık sadece website ürünü anlamına gelir.

**Kling video üretimi maliyet modeli (güncellendi):** Higgsfield yerine doğrudan Kling.ai kullanılacak (Standard plan, $6.99/ay ilk ay, 660 kredi, 720p sessiz modda ~30 kredi/5sn video — 1080p'ye gerek yok, zaten `kling_to_frames.py` kareleri 1280px'e ölçekliyor). **Eski "3D=sektör-bazlı tekrar kullanım" kuralı artık geçerli DEĞİL** (her tier müşteri fotoğrafı kullandığı için jenerik/tekrar-kullanılabilir video kalmadı) — yeni model: maliyet tier'e göre artıyor, fiyat da orantılı artıyor (B=Kling yok/~sıfır maliyet, A=kısa klip/düşük maliyet, S=tam video/orta maliyet, S+=en çok Kling çağrısı/en yüksek maliyet ama en yüksek fiyat da S+'da). Talep artınca Kling planı büyütülür (Standard→Pro→Premier→Ultra) veya tek seferlik kredi paketi alınır.

**S3 — Bot + Reklam + CRM (Hafta 4-5) — erken hazırlık, sırayı bilerek atladık**
- [~] 25. dm-qualifier ses/ton/ikna skill'i — `.agents/skills/turkce-nlp-satis-hitabet/SKILL.md` yazıldı (Chatwoot kurulumundan ÖNCE, kullanıcı isteğiyle). `cold-email` skill'inin prensipleri (akran gibi yaz, kanıta dayalı kişiselleştirme) + `/last30days` ile derinlemesine araştırılan gerçek NLP ikna teknikleri (mirroring/pace-matching, gömülü öneri vs. zorlayıcı komut ayrımı, zayıflatıcı kelimelerden kaçınma, sessiz lead'i reaktivasyon sorusuyla canlandırma) + isim öğrenilince Bey/Hanım hitabına geçme kuralı birleştirildi. `draft_outreach.py`'daki "uydurma isim / sahte aşinalık yasak" kuralı bu skill'e de taşındı. Gerçek müşteri sohbet örnekleriyle kalibrasyon için bilerek boş placeholder bırakıldı (uydurma örnek YOK) — kullanıcı ileride gerçek transkript paylaşınca doldurulacak.
- [~] Yanıt zamanlama (mirroring) mekanizması — `agents/ajan2/response_timing.py`: ilk temas 60-90sn bekleme; müşteri bizim gecikmemizden daha hızlı cevap verirse bir sonraki gecikmeyi 20sn düşür; yine hızlı cevap verirse 10-15sn'ye in (bir kademe hızlanınca geri yavaşlamıyor — rapport bozulmasın diye). State `leads.response_stage` + `leads.last_delay_seconds` kolonlarında tutuluyor (`supabase/migrations/002_conversation_timing_and_sales_tier.sql`, `schema.sql`'e de işlendi). DB'ye dokunmadan mantık testiyle doğrulandı; gerçek WhatsApp botuna henüz bağlanmadı (madde 26-27'yi bekliyor).
- [~] Sohbet-içi satış-tier'i (2026-07-19 güncellemesi: eski "Tier S = satış" adı **potansiyel_musteri** oldu) — `agents/ajan2/score_conversations.py`: `leads.tier` (eski_sistem/ortalama/iyi, iş fırsatı değeri, ÖNCEDEN hesaplanır) ile KARIŞTIRILMAMALI — bu, sohbet ilerledikçe müşteri mesajlarındaki sinyallere göre güncellenen ayrı bir eksen (`leads.sales_tier`: sadece_merak/kararsız/soğuk_satış/potansiyel_olabilir/potansiyel_musteri). Artık GEREKLİLİK-TABANLI: `potansiyel_musteri` olmak için 3 bağımsız gereklilik (sistemi_biliyor/istiyor/ariyor_sorunu_var) aranıyor, eksik olan gerekliliği hedefleyen somut aksiyon üretiliyor. Türkçe anahtar-kelime kural tabanlı sınıflandırıcı, `agents/ajan2/test_score_conversations.py` ile 11 senaryoyla test edildi — hepsi doğru tier'a düştü. Henüz gerçek sohbet verisi yok, madde 26-27 tamamlanıp ilk yanıtlar gelince gerçek anlamda çalışacak.
- [ ] 26-27. Chatwoot + Evolution API (WhatsApp) kurulumu — henüz başlanmadı; yukarıdaki iki mekanizmanın gerçek trafikte çalışması için ön koşul. Tamamlanınca sıra: ilk 10 taslak kullanıcıyla birlikte elden geçirilecek, sonra varyasyonlarla en iyi 5 "hooklayan" mesaj bulunacak (madde 14'teki plan).
- [~] s3-5. Randevu → takvim otomasyonu (2026-07-20) — `agents/ajan2/calendar_booking.py`: Google Calendar API (ücretsiz, faturalama gerekmez) + servis hesabı (OAuth giriş akışı YOK — ayrı bir "Randevular" takvimi servis hesabıyla paylaşılıyor) kullanılarak, dm-qualifier'ın "SPESİFİK gün/saat öner" NLP kuralına (açık uçlu "ne zaman uygunsunuz" değil) uygun şekilde 2-3 somut müsait saat öneren ve müşteri seçince gerçekten takvime yazan bir modül. Saf mantık (`compute_free_slots`, `format_slot_offer`) ile gerçek Google API çağrıları (`fetch_busy_periods`, `book_appointment`) bilerek ayrı tutuldu — `agents/ajan2/test_calendar_booking.py` ile 8 senaryoyla (boş gün, dolu saat, Pazar günü, bugünün 2-saat-sonrası kuralı, teklif formatı) test edildi, hepsi geçti. **Henüz gerçek Google Cloud servis hesabı kurulmadı** (kullanıcının yapması gerekiyor, `.env.example`'a adımlar + placeholder eklendi) ve madde 26-27 (Chatwoot/WhatsApp) tamamlanmadan canlı sohbete bağlanamaz.
- [~] s3-6. NocoBase pipeline panelini aç (2026-07-16) — `nocobase/` altında kuruldu (yerel, `.gitignore`'da — 65MB+ node_modules, tool klonlarıyla aynı muamele). **Önemli bulgu:** ücretsiz/açık kaynak NocoBase'de dokümantasyonun aksine "External PostgreSQL" veri kaynağı bağlayıcısı YOK (97 eklenti tarandı, yok) — bu özellik NocoBase'in ücretli dağıtımında. Çözüm: NocoBase'in kendi sistem tablolarını Supabase Postgres'teki **izole `nocobase` şemasına** kurduk (DB_SCHEMA env var ile), `public` şemasındaki `leads`/`businesses`/vb. tablolara dokunmuyor. Güvenlik önce zararsız bir test tablosuyla doğrulandı (okuma/yazma çalıştı, gerçek tablo şeması hiç değişmedi), SONRA gerçek `leads` tablosu "mevcut koleksiyon" olarak kaydedildi (schema:"public", autoGenId:false — NocoBase'in kendi ID/timestamp mantığını dayatmıyor). Kanban için gereken sıralama alanı `leads.kanban_sort` (bigint) migration ile eklendi (`supabase/migrations/005_leads_kanban_sort.sql`). "Lead Pipeline" adında bir sayfa + kanban bloğu (grupla: `status`) NocoBase API'si üzerinden (tarayıcı eklentisi bağlı olmadığı için) oluşturuldu; veri sorgusu doğrulandı ama görsel render kullanıcı tarafından `http://localhost:13000` üzerinden teyit edilmeli. **4 kapatıcıya hesap açma** kısmı henüz yapılmadı — gerçek çalışanlar işe alınınca (s3-7) yapılacak.
- [x] s3-8. Sözleşme şablonunu hazırla (2026-07-20) — `contracts/sozlesme-sablonu.md`: taraflar, hizmet kapsamı (B/A/S/S+ tier seçim kutucukları + güncel fiyat aralıkları), müşteriden beklenen girdiler (fotoğraf/işletme bilgisi), teslim süresi, revizyon hakkı, ödeme koşulları, yıllık hosting-bakım (3.000 TL), opsiyonel SEO 2.0 eklentisi, fikri mülkiyet devri, KVKK, cayma/fesih, sorumluluk sınırlaması, uyuşmazlık çözümü maddeleri. **Hukuki danışmanlık DEĞİL** — dosyanın başında avukat kontrolü önerisi açıkça belirtildi, tüm değişken alanlar `[...]` ile işaretli doldurulacak şekilde bırakıldı.
- [x] s3-9. Fiyat kademelerini yaz (2026-07-16) — **3D Web Sitesi: 12.000 TL, 7D Web Sitesi: 24.000 TL, yıllık hosting-bakım: 3.000 TL/yıl** (statik site, maliyet ~sıfır, saf marj). PDF'in kendi taslağı (10-15k/20-30k/35-60k TL) referans alındı, kullanıcı "10 ile 30 arasında olsun" dedi. `agents/ajan1/score_leads.py`'daki `DEFAULT_DEAL_VALUE` placeholder'ı (A=25k/B=15k/C=10k) gerçek rakamlarla güncellendi: **A=24.000 (7D'ye yatkın), B=18.000 (karışık), C=12.000 TL (3D'ye yatkın)** — bunlar tier bazında beklenen/karışık değer, kesin ürün seçimi konuşma sırasında belli oluyor. Mevcut leadlerin DB'deki `estimated_deal_value`'su da geriye dönük güncellendi (o an bilinen 1000 lead için; s1-7'de pagination hatası düzeltilip `score_leads.py` yeniden çalıştırılınca gerçek 2243 lead'in hepsi zaten güncel fiyatlarla yazıldı, ekstra backfill gerekmedi). `.agents/skills/turkce-nlp-satis-hitabet/SKILL.md`'nin Hizmetlerimiz bölümüne de fiyatlar işlendi.

**Ek/genişletilmiş kapsam (plan dışı ama konuşulan):**
- [x] `bexi-app/` Next.js PWA iskeleti (henüz sohbet arayüzü/API route yazılmadı, plan mission-control öneriyordu — henüz karşılaştırılmadı)
- [ ] `oh-my-claudecode` + ccr uyumluluk testi (Ajan 3 için)
- [ ] Cortex (GPT kod denetçisi) — hiç başlanmadı
- [ ] Frontend/Backend ayrı İnşaatçı rolleri — hiç başlanmadı
- [ ] mem0 (Yönetici uzun vadeli hafıza) — hiç başlanmadı

## Güvenlik notları

- Tüm API key'leri `.env`'de, asla commit edilmiyor (`.gitignore` içinde `.env`, `.env.*`, `!.env.example`)
- `ark-system` reposu **private**
- Ses/animasyon/gesture-activation gibi genişletilmiş "Jarvis" fikirleri bilinçli olarak
  kapsam dışı bırakıldı (ayrı, büyük bir proje olurdu) — Bexi şimdilik yazılı/basit tutuluyor
