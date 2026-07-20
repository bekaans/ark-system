# Katalog/Portföy Referans #3: otsuka-air.jp (/zeroz)

**Ne oldugu:** Otsuka Pharmaceutical'in (Otsuka Seiyaku - Japonya'nin
buyuk ilac/saglik urunleri sirketi) "/zeroz" (Active Inner Resource) adli
saglik takviyesi urunu icin yaptigi tek-urun tanitim/hikaye sitesi.

**Kullanicinin degerlendirmesi:** "harika bir urun portfoy gosterimi icin
olusturulacak bir site." Bu, "cok sayida farkli urun" gostermekten cok,
**TEK bir urunu COK DERINLEMESINE, hikaye anlatarak** tanitan bir format -
"portfoy" anlaminda urunun farkli kullanim senaryolarini/bilimsel
arka planini/faydalarini kapsamli sekilde sergiliyor.

## Dogrulanmis Teknoloji

- **Lenis** (smooth-scroll kutuphanesi) - dogrulandi, bu yuzden JS
  `window.scrollTo()` ile ani atlama YETERSIZ KALDI, gercek fare tekerlegi
  (wheel) olaylari gerekiyordu (Lenis kendi ic "yumusatilmis" scroll
  durumunu sadece gercek wheel input'una gore guncelliyor)
- **Three.js** (HTML kaynaginda referans bulundu) - muhtemelen arka planda
  ince bir 3D/parcacik efekti icin, ana gorsel deneyim DOM/CSS tabanli
- Toplam sayfa yuksekligi **~39,822px** - COK uzun, tek bir "hikaye"
  akisi olarak tasarlanmis
- 1 canvas elementi

## Gozlemlenen Tasarim (scroll ilerledikce)

### 1. Cok-Katmanli Pinlenmis Marka Logosu
Buyuk "/zeroz" kelime-logosu (once gri, sonra beyaza donusen bir fade-in
ile) ekranda UZUN SURE SABIT (pinned) kaliyor - klasik GSAP ScrollTrigger
"pin" teknigi (bizim `canvas-frame-sequence.ts`'de kullandigimizla ayni
prensip).

### 2. Yasam-Tarzi Fotograflari Logonun Icine/Ustune Biniyor
Pinlenmis logo devam ederken, GERCEK URUN KULLANIM fotograflari (bir
kadinin urunu cantasinda tasidigi kentsel bir sahne, sonra bir kisinin
dag/doga yuruyusunde urunu cikardigi bir sahne) logonun UZERINE, kucuk bir
kare cerceve icinde beliriyor - ayni "/zeroz" yazisi arka planda kalirken
farkli kullanim senaryolari sirayla "sahne degistiriyor."

### 3. Cift-Renkli Tipografi Katmani
Bazı anlarda AYNI logo iki farkli renkte (yesil + beyaz) hafif kaydirilmis
iki katman halinde ustuste biniyor - "Active Inner Resource ゼロズ" alt
basligiyla birlikte - zarif bir "double-exposure" tipografi efekti.

### 4. Bilimsel/Icerik Anlatimi
Fotograf sahnelerinin arasinda, urunun BILIMSEL ARKA PLANINI anlatan
Japonca metin blocklari beliriyor (ornek: "insanin yasamasi icin gerekli
oksijen... Otsuka'nin ulastigi 'oksijeni aktif kullanma' bitkisel bilesen
Kaempferol..." gibi) - urunun aktif bilesenini/bilimini anlatiyor.

### 5. Alt Ilerleme Cubugu (Section Pill) + Sag Nokta Navigasyonu
Ekranin altinda yesil bir "hap" (pill) sekli icinde o anki bolumun adi
goruntuleniyor ve scroll ilerledikce METIN DEGISIYOR: "About / Concept" ->
"About / Oxygen & Energy" -> "Science & Technology" - kullaniciya "hangi
bolumdesin" bilgisini surekli veriyor. Sag kenarda kucuk nokta
gostergeleri (pagination dots) ayni amaca hizmet ediyor.

## ARK'in Urun Yelpazesi Icin Anlami

Bu format, **TEK BIR URUN/HIZMETI DERINLEMESINE ANLATMAK ISTEYEN**
musteriler icin ideal (örn. imalatçı bir marka, ozel bir urun lansmani,
"amiral gemisi" bir hizmet). Onceki referanslardan (robinpayot, ujjwalagarwal)
FARKLI bir S+ yaklasimi: agir 3D/WebGL sahne yerine, **pinlenmis
tipografi + degisimli fotograf + anlatı metni + ilerleme gostergesi**
kombinasyonu - GSAP ScrollTrigger pin + Lenis smooth-scroll ile
ulasilabilir, bizim mevcut template altyapimiza (`canvas-frame-sequence.ts`
zaten pin+scrub kullaniyor) COK YAKIN, ekstra bir 3D motoru gerekmiyor.

**Somut ARK uygulamasi:** Bir musterinin AMIRAL GEMISI urunu/hizmeti icin
(ornegin bir restoranın imza yemegi, bir emlak firmasinin flagship
projesi) benzer bir "pinlenmis marka adi + donen kullanim senaryosu
fotograflari + hikaye anlatan metin + ilerleme cubugu" formati
kurulabilir.

**Kaynak:** https://otsuka-air.jp/
