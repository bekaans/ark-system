# A-Tier Referans #1: controleur.ca

**Ne oldugu:** "Le Contrôleur" - Quebec/Kanada merkezli, buyuyen hizmet
KOBI'leri icin finansal yonetim/kontrolluk hizmeti veren bir B2B sirketin
kurumsal sitesi.

**Kullanicinin degerlendirmesi:** "tam A tier bir site, oyun haline
dondurulmemis ama genis animasyonlar ve efektler ile urun tanitimi icin
muhtesem ve muhtemelen en cok satacagimiz site modeli olacaktir." Yani bu,
S+/7D (Three.js/WebGL bespoke) tier'in ALTINDA ama "classic/basit" tier'in
USTUNDE, iş dunyasina uygun, pratik ve tekrar uretilebilir orta seviye.

## Dogrulanmis Teknoloji

Script host'lari incelendi:
- `static.hsappstatic.net` - **HubSpot CMS** kullanildigini gosteriyor (bu
  kesin bir HubSpot imzasidir)
- `static.hotjar.com` / `script.hotjar.com` - Hotjar (kullanici davranis
  analitigi/isi haritasi)
- `www.googletagmanager.com`, `googleads.g.doubleclick.net` - GTM + Google
  Ads izleme
- `cdn-cookieyes.com` - CookieYes (cerez onay banner'i)
- **0 canvas elementi** - WebGL/Three.js YOK, standart HTML/CSS/SVG +
  HubSpot'un kendi tema modul sistemi ile calisiyor

**Onemli sonuc:** Bu site bespoke bir muhendislik urunu DEGIL, HubSpot CMS
gibi kurumsal/standart bir platform uzerine kurulu - yani ARK'in bu tier'i
COK DAHA HIZLI VE UCUZ URETEBILECEGI, olcek-lenebilir bir model demek
(Three.js sahnesi degil, duzenli HTML/CSS + scroll-reveal animasyonlari).

## Gozlemlenen Tasarim

1. **Hero:** Sol tarafta buyuk, net baslik ("Gestion financière complète
   pour **les PME de services en croissance**" - anahtar kelime mavi renkle
   vurgulanmis), alt yazi + "Planifier un appel" CTA butonu. Sag tarafta
   ISOMETRIK 3D-gorunumlu (ama aslinda duz illustrasyon/SVG, gercek 3D degil)
   bir sahne: borular, disliler, robot kamera, ag/network noktalari,
   takvim, dolar isareti, pasta grafik, indirim/hediye ikonu - finansal
   yonetim temasini simgeleyen dekoratif kompozisyon.
2. **Ikinci bolum:** "On vous aide à répondre à ces questions grâce à des
   chiffres fiables" basligi + checklist (mavi tik ikonlu) madde listesi +
   arka planda hafif animasyonlu sari/turuncu blob sekli.
3. Sabit (sticky) ust navigasyon, temiz acik mavi/beyaz renk paleti.

## ARK'in Urun Yelpazesi Icin Anlami

Bu, S+ (7D, Three.js) ile "classic" (basit, statik) arasinda **orta/en
cok satacak tier** icin somut bir hedef: HubSpot-tarzi kurumsal temizlik +
tasteful (agir olmayan) scroll-reveal animasyonlari + net CTA odakli
yapi. Bizim GSAP canvas-frame-sequence altyapimizla bu seviye zaten
ulasilabilir - bu tier icin ekstra bir 3D motoruna GEREK YOK, mevcut
sablon motorumuz (`template/app`) dogru araç.

**Kaynak:** https://controleur.ca/
