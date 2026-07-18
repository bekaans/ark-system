---
name: ARK Vitrin Sablonu v1
description: Sektore gore uyarlanabilir, scroll-scrubbing animasyonlu yerel isletme vitrin sitesi
colors:
  ink: "#1d1d1f"
  accent: "#ff9500"
  surface: "#fafafc"
  surface-card: "#ffffff"
typography:
  display:
    fontFamily: "Poppins, sans-serif"
    fontSize: "clamp(2rem, 6vw, 4rem)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "normal"
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: "12px"
  pill: "999px"
spacing:
  sm: "1rem"
  md: "1.5rem"
  lg: "4rem"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.pill}"
    padding: "0.9rem 2rem"
  service-card:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "1.75rem"
---

# Design System: ARK Vitrin Sablonu v1

## 1. Overview

**Creative North Star: "The Sector Mirror"**

Bu sablon kendi kimligini dayatmaz - her isletmenin sektorune gore renk ve
karakter degistiren bir ayna gibi calisir. Bir oto galerisi ile bir kuafor
salonu ayni "sablon" gibi hissettirmemeli; `site.config.json`'daki
`design.primary_color`/`design.secondary_color` alanlari her musteri icin
farkli bir yuzey yaratir, ama ALTTAKI yapisal iskelet (tipografi olcegi,
bilesen sekilleri, hareket dili) sabit kalir. Bu dokuman o sabit iskeleti
tanimlar - renkler burada bir ORNEK (oto galerisi), kural degil.

Bu sistem acikca REDDETTIGI seyler: jenerik "AI-yapti sablon" hissi -
gradient text, her bolumde ayni kucuk-harfli "eyebrow" etiket, cream/sand/bej
varsayilan renk paleti, ozdes kart izgaralari, hero-metric sablonu. Ayrica
genel "kurumsal stok fotograf" hissini de reddeder - gorseller (Higgsfield
uretimi, s2-3) her zaman o spesifik isletmeye ait olmalidir.

**Key Characteristics:**
- Renk sektore gore degisir, yapi degismez
- Scroll-scrubbing animasyon dekoratif degil, hikaye anlatma araci
- Bilesenler dokunsal ve enerjik - "satis" hissi, "kurumsal broşür" degil
- Telefonda hizli karar veren ziyaretci icin: CTA her zaman bir kaydirma uzaginda

## 2. Colors

Palet, ORNEK musteri (Ornek Oto Galeri) icin secilmis - her gercek musteride
`site.config.json` uzerinden degisir. Yapisal rol (ink/accent/surface) sabit
kalir, hex degerleri degisir.

### Primary
- **Charcoal Ink** (#1d1d1f): Govde metni, hero uzerindeki metin golgesi,
  iletisim bolumu arka plani. Sektorden bagimsiz "guven" tasiyan sabit koyu ton.

### Secondary
- **Signal Amber** (#ff9500): CTA butonu, testimonial yazar adi, vurgu
  ogeleri. Sektore gore degisir (orn. bir kuafor icin pembe/mor olabilir) -
  ama HER ZAMAN "sadece bir eylem noktasinda" kullanilir, govde metninde asla.

### Neutral
- **Off-White Surface** (#fafafc): Hizmet izgarasi ve sosyal kanit
  bolumlerinin arka plani - saf beyazdan (#ffffff, kart yuzeyi) hafifce
  ayristirilmis, boylece kartlar yuzeyden kalkar.
- **Pure Card White** (#ffffff): Hizmet karti arka plani.

### Named Rules
**The Signal Rule.** Accent renk (amber/sektore-ozel-renk) sadece EYLEM
noktalarinda kullanilir (CTA butonu, tek bir vurgu) - govde metninde,
arka planda, veya dekoratif olarak asla. Yuzeyin %10'undan azini kaplar.

## 3. Typography

**Display Font:** Poppins (sans-serif fallback)
**Body Font:** Inter (sans-serif fallback)

**Character:** Poppins'in geometrik, kendinden emin agirligi baslıklarda
"bu isletme ciddiye aliniyor" hissi verir; Inter'in notr okunabilirligi govde
metninde dikkat cekmeden bilgiyi tasir - kontrast ekseni (geometrik + notr
humanist), iki benzer sans-serif cakismasindan kacinir.

### Hierarchy
- **Display** (700, `clamp(2rem, 6vw, 4rem)`, 1.1): Hero baslik - tek basina,
  sayfada sadece bir kez.
- **Body** (400, 1rem, 1.5): Govde metni, hizmet aciklamalari, testimonial.

### Named Rules
**The One Display Rule.** `clamp()` display boyutu sayfada SADECE hero
baslikta kullanilir - hizmet karti basliklari (h3) her zaman kucuk, sabit
boyutta kalir. Iki farkli olcekte "buyuk baslik" ayni ekranda olmaz.

## 4. Elevation

Sistem hafif katmanli (tonal layering + tek bir yumusak golge) - agir,
"2014-tarzi" sert golgeler yok. Kartlar yuzeyden HAFIFCE kalkar, ama
golge asla kendini belli eden bir cerceve gibi hissettirmez.

### Shadow Vocabulary
- **card-rest** (`box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.04)`):
  Hizmet kartlarinin varsayilan durumu - cift katmanli, yakin+uzak golge.
- **card-hover** (`box-shadow: 0 4px 12px rgba(0,0,0,0.10), 0 16px 40px rgba(0,0,0,0.08)`):
  Hover'da golge derinlesir + karti 4px yukari kaldirir (`translateY(-4px)`) -
  "dokunsal ve enerjik" bilesen hissi icin kasitli, belirgin bir tepki.

### Named Rules
**The Single Shadow Rule.** Her bilesen tipinin (kart, buton) TEK bir
golge kimligi vardir (rest + hover cifti). Farkli bilesenler farkli golge
degerleri icat etmez - ayni iki degeri paylasir.

## 5. Components

### Buttons
- **Shape:** Tam pill (`border-radius: 999px`)
- **Primary:** Accent arka plan (#ff9500), beyaz metin, `padding: 0.9rem 2rem`,
  600 agirlik. Dokunsal ve enerjik: hover'da hafif buyume
  (`transform: scale(1.04)`) + arka plan bir ton koyulasir.
- **Hover / Focus:** `transition: transform 0.2s ease-out, background 0.2s`;
  focus-visible'da 2px beyaz + 2px accent cift-halka outline (erisilebilirlik).

### Cards / Containers
- **Corner Style:** 12px (`--rounded-sm`) - "kart" hissi verir ama asiri
  yuvarlak degil (impeccable'in 32px+ yasagi ile uyumlu).
- **Background:** Pure Card White (#ffffff) yuzeyin uzerinde (Off-White Surface).
- **Shadow Strategy:** bkz. Elevation - rest/hover cifti.
- **Border:** Yok - derinlik golgeyle saglanir, kenarlikla degil.
- **Internal Padding:** 1.75rem.
- **Hover davranisi (dokunsal ve enerjik):** `translateY(-4px)` + golge
  derinlesmesi + 0.25s ease-out-quart gecis. Bounce/elastic YOK.

### Navigation
Bu v1'de ayri bir navigasyon bileseni yok (tek sayfa, scroll-tabanli akis) -
tek CTA iletisim bolumunde. Gelecek surumlerde (s2-6+) sabit bir "WhatsApp'tan
Yaz" mini-CTA'si scroll ile birlikte gorunur kalabilir (henuz uygulanmadi).

### Canvas Frame-Sequence (Signature Component)
Hero ve 2. animasyon bolumlerindeki scroll-scrubbing canvas - bu sistemin
imza bileseni. Scroll pozisyonu (0-1) dogrudan kare indeksine baglanir
(GSAP ScrollTrigger, `pin: true, scrub: true`). Reduced-motion tercih eden
kullanicilar icin: `prefers-reduced-motion: reduce` durumunda pinleme/scrub
yerine tek bir statik kare (ortadaki kare) gosterilmeli (henuz uygulanmadi -
bkz. Do's and Don'ts).

## 6. Do's and Don'ts

### Do:
- **Do** accent rengi (sektore gore degisen) SADECE tek bir eylem noktasinda
  kullan (CTA, vurgu) - yuzeyin %10'undan az.
- **Do** kart/buton hover'larinda belirgin ama sert-olmayan tepki ver
  (`translateY(-4px)`, `scale(1.04)`, ease-out-quart) - "dokunsal ve enerjik"
  hissi icin bu KASITLI, "sakin" degil.
- **Do** her sektor icin `site.config.json` uzerinden renk/icerik degistir,
  yapisal iskeleti (tipografi olcegi, bilesen sekilleri) sabit tut.
- **Do** govde metnini govde-arka-plan kontrastinda >= 4.5:1 tut (Charcoal Ink
  #1d1d1f, Off-White #fafafc uzerinde bu esikten fazlasiyla yukarida).

### Don't:
- **Don't** gradient text kullanma (`background-clip: text` + gradient) -
  vurguyu agirlik/boyutla yap.
- **Don't** her bolume kucuk-harfli, genis-araliklı bir "eyebrow" etiketi
  ekleme (01/02/03 numaralandirma dahil) - bu 2023-donemi AI-sablon izi.
- **Don't** cream/sand/bej varsayilan govde arka plani kullanma - bu sistemde
  govde arka plani ya saf beyaz/off-white (chroma 0'a yakin) ya da isletmenin
  KENDI marka rengi, "sicak" oldugu icin degil.
- **Don't** ozdes, sinirsiz tekrarlanan kart izgaralari kurma - hizmet
  izgarasi en fazla 3-4 kart, her biri farkli bir gercek hizmeti temsil eder
  (uydurma "ozellik" doldurma yok).
- **Don't** `border-left`/`border-right` > 1px'i renkli bir vurgu cizgisi
  olarak kullanma.
- **Don't** scroll-scrubbing animasyonunu `prefers-reduced-motion: reduce`
  kontrolu olmadan birak - bu v1'de eksik, s2-4/polish gecisinde eklenmeli.
