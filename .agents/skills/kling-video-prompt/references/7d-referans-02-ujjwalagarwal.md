# 7D Referans #2: ujjwalagarwal.com

**Ne oldugu:** Ujjwal Agarwal'in ("Generative Artist / Creative Technologist /
Educator", Bangalore merkezli) kisisel portfolyo sitesi. Generative art,
real-time enstalasyon ve ses uzerine calisan bir sanatci/teknolog.

**Kullanicinin degerlendirmesi:** "animasyonlari muhtesem olmus" - S+ class
referans (robinpayot.com ile ayni ust seviye kategoride).

## Dogrulanmis Teknoloji Yigini

Sayfa scriptleri toplu cekilip (~1.68MB) icerik tarandi, kesin sonuc:

- **Next.js** (Turbopack bundler ile - `_next/static/chunks/turbopack-*.js`)
- **GSAP + ScrollTrigger** - scroll-tetiklemeli animasyonlar
- **Lenis** - yumusak/virtual scroll kutuphanesi (native scroll'u
  "yumusatarak" yeniden yorumluyor - bu yuzden basit `Page_Down` tusu ilk
  denemede calismadi, `window.scrollTo()` ile calisti)
- **p5.js** - generative/2D canvas sanat kutuphanesi (muhtemelen ASCII/nokta
  deseni portre efekti bunula yapiliyor)
- **Three.js + React Three Fiber** - 3D/WebGL parcalari icin (muhtemelen
  proje alt-sayfalarindaki enstalasyon gorsellestirmelerinde)
- 1 adet `<canvas>` elementi tespit edildi (ana sayfada)

## Gozlemlenen Efektler

### 1. ASCII/Yaricik Desenli Portre - Ilerlemeli Renk Doldurma
Sayfa ilk acildiginda kirmizimsi-bej arka planda, yaricik/nokta deseniyle
cizilmis (halftone tarzi) soluk bir yuz portresi goruniyor. Kullanici scroll
ettikce (veya sayfa yuklendikce) portrenin alt kismindan itibaren altin/sari
bir renk "doluyor" - kademeli bir reveal/fill animasyonu. **Muhtemel teknik:**
p5.js ile canvas uzerinde piksel/nokta yogunluguna gore render edilen bir
portre + scroll/zaman ilerledikce maskelenen bir renk katmani.

### 2. Canli Saat (tematik detay)
Sol ustte "BLR HH:MM:SS" seklinde GERCEK ZAMANLI, saniyede guncellenen bir
saat var (Bangalore saati). Footer'da "TIME IS THE MEDIUM." yaziyor - saat
sadece dekoratif degil, sanatcinin "zaman" temasiyla bilincli baglanmis.
**ARK icin ders:** Kucuk, anlamli, tema ile tutarli bir detay (canli saat,
canli hava durumu, vb.) buyuk bir WebGL sahnesinden daha az maliyetli ama
"bu site ozenle dusunulmus" hissi yaratiyor.

### 3. Blur-Out Scroll Gecisi
Bir bolum yukari kayip ekrandan cikarken net bir sekilde BULANIKLASIYOR
(blur filtresi artarak), yeni bolum netleserek geliyor. Duz bir fade/opacity
gecisinden daha "sinematik" hissediyor. **Muhtemel teknik:** GSAP
ScrollTrigger ile scroll pozisyonuna bagli `filter: blur(Npx)` degeri
animasyonu.

### 4. Zarif Tipografi Karisimi
Isim basligi iki farkli font stilinin karisimi: "Ujjwal" duz/blok serif,
"Agarwal" el yazisi/italik script font - ayni basliginda iki karakter
birlesimi zarif bir kontrast yaratiyor.

### 5. Numarali Proje Listesi
Proje bolumu numaralandirilmis (06, 07, 08...), her satirda proje adi (buyuk
serif baslik) + kisa aciklama cumlesi + sag tarafta kategori/yil etiketleri
(orn. "AUDIO-VISUAL INSTALLATION / REAL-TIME - SENSOR - 2024"). Ince yatay
cizgilerle ayrilmis, bol bosluklu, sade.

### 6. Kapanis
"Say hello." buyuk baslik + iletisim bilgisi (e-posta, sehir) + telif hakki
+ tematik kapanis cumlesi ("TIME IS THE MEDIUM."). Ayrica "ENTER THE ORDER"
diye ayri bir generative-art projesine gecis linki var.

## ARK'in 7D Urunune Uygulama Notu

Bu site, Robin Payot ornegine gore DAHA AZ agir/WebGL-yogun ama esit derecede
"S+ class" hissi veriyor - cunku detaylar (canli saat, blur gecisleri,
tipografi, ilerlemeli portre reveal'i) buyuk bir 3D sahneden daha ucuz
uretilebilir ama ozenli/premium hissi ayni derecede guclu. **Bu, 7D urunu
icin ikinci bir "S+ tier" yaklasimi olarak dusunulebilir:** tam Three.js
flythrough (robinpayot tarzi) yerine, GSAP+Lenis+p5.js ile daha hafif ama
yine de "muhtesem" hissettiren bir animasyon seti.

**Kaynak:** https://www.ujjwalagarwal.com/
