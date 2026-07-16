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
| Groq (`llama-3.3-70b-versatile`) | dmq/Bexi birincil | 1.000 istek/gün, düşük gecikme | ✅ test edildi |
| Google AI Studio (Gemini) | Yedek katman (çoğu ajan) | 1.500 istek/gün/model | ⚠️ flash-lite ✅, tam flash geçici 503 verdi (Google tarafı) |
| OpenRouter (çeşitli `:free`) | Son çare yedek | Hesap-bazlı paylaşımlı 50/gün (kredi yoksa) | ✅ Nemotron modelleri calisti, Llama 3.3 free rota gecici 429 (Venice saglayici, hesabimizla ilgisiz) |
| OpenRouter (`deepseek/deepseek-v4-pro`) | Bexi birincil | Ücretli, ~$0.435/$0.87 per 1M token | ⏳ hesaba bakiye yüklenmedi, test edilmedi |
| Anthropic (`claude-haiku-4-5-20251001`) | dmq/Bexi **son çare** fallback | Ücretli | ⏳ key eklendi ama bilinçli olarak **bakiye yüklenmedi** — sadece 3 ücretsiz katman da çökerse tetiklenir, gereksiz yere para yatırılmadı |

**Not:** Plandaki S0/6 maddesi Claude API'yi dm-qualifier ve Yönetici'nin "beyni" olarak
varsayıyordu (ücretsiz zincir değil). Karar: Anthropic key'i plana uymak için eklendi ama
maliyeti sıfırda tutmak için sadece son-çare fallback yapıldı — gerçek trafik gösterip
ihtiyaç doğarsa bakiye yüklenecek.

## Kurulum durumu

**S0 — Marka + Altyapı**
- [x] 1. Domain + marka araştırması — **arkintelligencelabs** olarak karar verildi (ilk denemede "arkintellenge" yazım hatası yapıldı, düzeltildi; ayrıca doğru yazım "arkintelligence.com" 2018'den beri başkasına ait ve 2033'e kadar kilitli olduğu için "labs" eklendi). Kayıt: turkticaret.net, uzantılar `.com` `.store` `.com.tr` `.online`, 1 yıllık, başlangıç 2026-07-16 (yenileme: 2027-07-16). Tümü müsaitlik kontrolünden geçti (whois ile doğrulandı).
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
- [x] 12. Site denetçisi — `agents/ajan1/audit_sites.py`, Playwright + regex tabanlı GSAP/Meta Pixel/gtag tespiti + basit SEO skoru (tam Lighthouse değil, hafif sezgisel skor). Ekran görüntüleri `agents/ajan1/data/screenshots/` (gitignore'da, ~37MB ham veri repoya girmiyor).
- [ ] 13-16. Lead puanlama + Tier atama, outreach taslakları, sürekli-çalışan döngü (gecelik değil, "açık olduğu sürece" - kullanıcı tercihi), ilk mesajlar — henüz başlanmadı

**Not:** Bu adımlar şu an **ben (Claude Code) tarafından elle çalıştırılıyor** — Ajan 1 henüz bağımsız/otomatik çalışmıyor. Madde 15'te (adı değişecek: "sürekli döngü") bu script'ler bir servise bağlanınca gerçek anlamda "Ajan 1 çalışıyor" denebilecek.

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
