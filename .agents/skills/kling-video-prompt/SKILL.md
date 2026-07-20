---
name: "kling-video-prompt"
description: "Kling 3.0 icin ARK'in B/A/S/S+ dinamik web sitesi vitrinlerini tanitan reels/pazarlama videolari VE A/S/S+ urunlerinin ozu olan 'musterinin gercek fotograflarini image-to-video ile animasyonlu dijital kimlige cevirme' isini yaparken kullanilacak prompt yapisi ve hazir sablonlar (2026-07-19: eski '3D'/'7D' tier isimleri B/A/S/S+ oldu, bkz README.md). 'kling prompt', 'reels video', 'vitrin videosu', 'tanitim videosu', 'dijital kimlik', 'higgsfield yerine' gecen her yerde devreye gir. s2-8 (her vitrin icin 1 reels) ve benzeri video uretim gorevlerinde kullan. Hedef-kalite referanslari icin bkz. references/7d-referans-*.md (kullanicinin onayladigi gercek site ornekleri, teknik analizli - dosya adlari tarihi, icerik hala gecerli)."
license: internal
metadata:
  version: 1.0.0
  author: ARK Intelligence Labs
  category: video-prompt
  updated: 2026-07-18
  research_basis: "WebSearch - Kling 3.0 prompting guide (fal.ai, kling.ai, magichour.ai) + Kling vs Seedance 2.0 karsilastirmasi"
---

# Kling 3.0 Prompt Sablonu (dinamik web sitesi vitrinleri icin)

ARK'in urettigi B/A/S/S+ dinamik web sitelerini (GSAP scroll-scrubbing animasyonlu)
tanitan kisa reels/pazarlama videolari icin Kling 3.0 prompt'lari yazarken kullan.
Kling secildi cunku (a) Seedance 2.0'a gore agirlikli hedefimiz olan "prompt'a
tam sadakat" konusunda daha guclu - istenmeyen "organik ekleme" yapmadan tam
istenen kamera hareketini/aksiyonu uretiyor, (b) native 4K/60fps veriyor, (c)
kredi basina Seedance'in ~4'te biri maliyetinde (bkz. proje maliyet notlari).

## Temel 5 Parcali Yapi

Her prompt bu sirayla yazilir, atlanan parca "belirsiz/rastgele" sonuc verir:

1. **Subject (konu)** - ekranda ne var: laptop/telefon mockup'i, uzerinde ARK'in
   urettigi web sitesi calisiyor
2. **Motion (hareket)** - konunun/animasyonun kendi hareketi: sayfa scroll'u,
   buton hover, canvas frame-sequence oynatimi
3. **Camera (kamera dili)** - kameranin hareketi, Kling bunu cok iyi anliyor:
   "slow dolly push toward subject", "smooth pan left to right", "steady
   tracking shot", "gentle tilt down"
4. **Scene/Environment (ortam)** - arkaplan: temiz stüdyo gradyani, minimal masa
   yuzeyi, karanlik oda + ekran isigi
5. **Style/Lighting (stil/isik)** - her videonun sonuna EKLENECEK sabit cumle,
   marka tutarliligi icin (asagida)

## Sabit Stil Kuyruk Cumlesi (her prompt'un sonuna ekle)

Marka tutarliligi icin HER prompt ayni stil cumlesiyle bitmeli:

> "cinematic lighting, clean modern studio background, shallow depth of field,
> high production value, sharp focus on screen content, subtle screen glow"

## Kamera Hareketi Kelime Dagarcigi

Belirsiz ifadeler ("kamera hareket ediyor") yerine KESIN yon/fiil kullan:

- `slow dolly push toward subject` - ekrana yavasca yaklasma (acilis icin iyi)
- `smooth pan left to right` - yatay tanitim taramasi
- `gentle tilt down from above to screen level` - yukaridan asagi inis
- `steady tracking shot following the scroll` - sayfa scroll'unu takip eden kamera
- `slow orbit around the device` - cihazin etrafinda donen kamera (3D/7D vurgusu icin)

Kling, "dolly forward" gibi net talimatlarda GERCEK parallax uretiyor (on plan
arka plandan daha hizli hareket eder) - bu yuzden vurgulanacak yer 3D/7D
derinlik hissi ise mutlaka bir dolly/orbit hareketi prompt'a dahil et.

## Coklu Sahne (Multi-Shot) Kullanimi

Kling 3.0 tek uretimde 6 sahneye kadar storyboard destekliyor. Tek bir vitrin
videosu icin 3 sahnelik yapi onerilir:

```
Shot 1 (0-2s): [acilis - dolly push, cihaz karanlik ekrandan aydinlanir]
Shot 2 (2-5s): [ana gosterim - tracking shot, site scroll animasyonu oynar]
Shot 3 (5-8s): [kapanis - slow orbit, ARK logosu/CTA ekranda]
```

Her sahneyi ayri ayri etiketleyip cerceve+konu+hareketini net tanimla - hepsini
tek paragrafa sikistirma.

## Hazir Sablon (kopyala-degistir)

```
Shot 1 (0-2s): Close-up of a dark laptop screen on a clean gradient studio
background, screen slowly powers on, subtle glow illuminates the desk surface.
Slow dolly push toward the laptop.

Shot 2 (2-5s): The laptop screen shows a modern animated website homepage
mid-scroll, smooth parallax scrolling animation playing, elegant motion
graphics. Steady tracking shot following the scroll motion, slight orbit to
reveal screen depth.

Shot 3 (5-8s): Camera pulls back in a slow orbit around the laptop, revealing
the full clean desk setup, website still glowing on screen. Gentle tilt up to
end on a wide, polished final frame.

cinematic lighting, clean modern studio background, shallow depth of field,
high production value, sharp focus on screen content, subtle screen glow
```

Degistirilecek yerler: laptop/telefon secimi, site turu (oto galeri, restoran
vb. - `site.config.json`'daki sektore gore), renk paleti (markanin/musterinin
renklerine gore gradyan degistir).

## Isletme Dijital Kimligi (image-to-video, GERCEK musteri fotograflarindan - A/S/S+ tier'lerin ortak teknigi)

Bu, A/S/S+ urunlerinin tam ozudur (2026-07-19: eski "7D'nin ozu" tanimi
genisletildi - artik B haric HER tier musteri fotografi kullaniyor, sadece
A'da KISA/hafif, S/S+'da TAM/govdeli uygulanir) ve yukaridaki jenerik
sablondan TAMAMEN FARKLI bir islemdir: metinden video uretmek degil,
**musterinin GERCEK fotografini** (isyeri girisi, urunler, ic mekan) girdi
olarak verip Kling'in image-to-video ozelligiyle bunu canlandirmak. Kling
burada METNI degil, VERILEN FOTOGRAFI hareket ettiriyor.

### Girdi Fotograf Hazirligi (kritik on kosul)

- **Cozunurluk:** en az 1024x1024, ideal 2048x2048 - dusuk cozunurluk kenar
  bozulmasina/artefaklara yol acar
- **Netlik:** iyi isikli, bulanik olmayan kare sart
- **Sade arka plan tercih edilir** - karmasik/kalabalik arka plan ongoremeyen
  hareket uretir; gerekirse musterinin fotografini once kirp/temizle
- Musterinin gonderdigi ham fotograflar cogu zaman bu sartlari karsilamaz -
  once bir on-isleme adimi (kirpma, hafif netlestirme) gerekebilir

### Prompt Formulu: "Subject + Movement"

Kling image-to-video icin resmi format: Kamera hareketi -> Konu+aksiyon ->
Ortam (fotografin orijinal ortamini KORU) -> Isik -> Stil -> Kisitlamalar
(negative prompt). "Subject + Movement" formulu (orn. "Mona Lisa elini
kaldirip gunes gozlugu takiyor") - net, tek bir hareket tarifi en iyi sonucu
verir.

### Ornek: Isyeri Girisi Fotografini Canlandirma

```
[Girdi: musterinin isyeri girisi fotografi]

Prompt: Slow dolly push toward the storefront entrance, gentle parallax as
camera moves closer, warm light gradually glows on inside the windows,
subtle breeze moves any visible signage or awning.

Camera: slow dolly push
Subject+action: storefront gradually comes to life, interior lights turning on
Environment: keep original photo's setting exactly as-is
Lighting: warm golden hour glow, intensifying over the clip
Style: cinematic, photorealistic, no stylization
Negative prompt: no warping edges, no jittery motion, no background
distortion, no logo/signage distortion, no face distortion
```

### Ornek: Urun Fotografini Canlandirma

```
[Girdi: musterinin urun fotografi]

Prompt: The product rotates slowly on its axis, soft rim lighting highlights
the edges, camera does a slow dolly in toward the product's key detail.

Environment: keep original background as-is
Style: cinematic, photorealistic
Negative prompt: no warping edges, no jittery motion, no background
distortion
```

### Kalite Kontrolu (her uretimden sonra kontrol et)

- Yuz/logo/tabela stabilitesi bozulmus mu?
- Arka planda warping/bozulma var mi?
- **Bir seferde TEK sorunu duzelt** - ayni anda hem kamerayi hem isigi hem
  hareketi degistirirsen hangisinin sorunu cozdugunu takip edemezsin

## Genel Kurallar

- **Basit basla, iterasyonla ilerle** - ilk denemede tum detaylari doldurmaya
  calisma, sonucu gorup ayarla.
- **Kling'i bir kamera ekibi gibi yonet** - "bu goruntuyu tarif et" yerine "bu
  sahneyi FILME AL" mantigiyla yaz (yonetmen gibi dusun).
- **Ise yarayan bir prompt'u kopyala, isim/palet degistir** - her yeni vitrin
  icin sifirdan yazmak yerine yukaridaki sablonun degisken kismini guncelle.
- **Sabit stil cumlesini asla atlama** - 6 vitrinin hepsi ayni "bakis" ile
  bitmezse marka tutarliligi kaybolur.
