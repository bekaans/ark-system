# Klasik/Uygun-Fiyatli Tier Referans #1: le-lab.io

**Ne oldugu:** "Le Lab" - Bordeaux (Fransa) merkezli, video/FPV-drone/tasarim
odakli bir yaratici stüdyonun tanitim sitesi.

**Kullanicinin degerlendirmesi:** "bu en basit yapacagimiz klasik bir site,
uygun fiyatli siteler bu tarz olacak" - yani S+/7D (Three.js) ve A-tier
(HubSpot-tarzi) ALTINDA, en giris seviyesi/en ucuz urun kategorisi icin
hedef referans.

## Dogrulanmis Teknoloji

- **Barba.js** (`data-barba="wrapper"` attribute'u dogrulandi) - sayfa
  gecislerini AJAX ile yumusatan bir kutuphane (tam sayfa yenilemeden
  gecis animasyonu)
- **AOS - Animate On Scroll** (`data-aos-easing`, `data-aos-duration`,
  `data-aos-delay` attribute'lari dogrulandi) - basit, hafif bir
  scroll-reveal kutuphanesi (elementler scroll ile goruncur alana girince
  fade/slide animasyonu)
- `onload="init()"` - custom vanilla JS baslatma fonksiyonu
- **0 tam-3D/WebGL katmani yok** - gorseller onceden render edilmis
  illustrasyonlar/gorunuyor (izometrik/3D-GORUNUMLU ama statik PNG'ler)

## Gozlemlenen Tasarim

Sicak sari/hardal rengi arka plan. Hero bolumunde: "LE LAB" buyuk, kalin,
3D-gorunumlu (govdeli/extruded) tipografi bir podyum/sahne uzerinde,
"STUDIO DE CRÉATION" alt yazisi podyumun on yuzunde. Sahne dekoru: stüdyo
isik ayaklari (softbox), ucan drone ikonlari, kamera/mikrofon gibi
ekipman prop'lari - hepsi ayni sicak sari/krem renk paletinde, illustre
tarzda (fotogerceki 3D degil, duz/stilize gorseller).

Navigasyon: Accueil, Vidéo, FPV & Drone, Design, Studio, Contact. Sag altta
kucuk "W. Honors" (Awwwards onur rozeti) sabit widget'i.

## ARK'in Urun Yelpazesi Icin Anlami

Bu tier'in teknik gereksinimi COK DUSUK: Barba.js (sayfa gecisi) + AOS
(scroll-reveal) - ikisi de hafif, kurulumu kolay, bakim maliyeti dusuk
kutuphaneler. Mevcut GSAP tabanli sablon motorumuz bu seviyeyi zaten
fazlasiyla karsiliyor - bu tier icin ekstra bir sey gelistirmemize gerek
yok, sadece illustrasyon kalitesi/tasarim ozenini bu seviyede tutmak
yeterli.

**Kaynak:** https://le-lab.io/
