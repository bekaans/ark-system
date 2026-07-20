# Katalog/Portföy Referans #1: Panasonic 電気設備BOX

**Ne oldugu:** Panasonic Japonya'nin B2B "elektrik tesisati/aydinlatma"
urun kataloglari icin yaptigi dijital showroom mikrosite'i
(`www2.panasonic.biz/jp/dsr/index/`).

**Kullanicinin degerlendirmesi:** "muhtesem otesi, kataloglar veya emlak
portfoyleri, arsa portfoyleri genel olarak katalog ve portfoy icin
muhtesem bir site" - yani bu, TEK BIR ISLETME KIMLIGI degil, **COK SAYIDA
URUN/ODA/OZELLIGI TEK GORSELDE GOSTEREN** bir format icin referans:
emlak portfoyleri (bir evin tum odalarini/ozelliklerini tek bakista
gostermek), arsa portfoyleri, urun katalogu sayfalari icin ideal.

## Yapı

Bu, TEK bir sayfa degil - bir **INDEX/HUB sayfasi** (`/jp/dsr/index/`) ve
oradan "VISIT SITE" ile acilan ayrintili alt-sayfalar (`/jp/densetsu/
e-kurashi/` gibi) seklinde. Index sayfasinin sag kenarinda COK SAYIDA
nokta (pagination dots) var - bu, ayni formatta baska "BOX" mikrositelerinin
de var oldugunu gosteriyor (farkli urun/konu kataloglari icin tekrarlanan
bir sablon).

## Gozlemlenen Tasarim (Index Sayfasi)

**Ana gorsel: Izometrik "kesit" ev illustrasyonu.** Bir evin/binanin katlari
kesitte gosteriliyor (izometrik/3D-gorunumlu ama duz vektor illustrasyon,
gercek 3D degil), her katta/odada kucuk KARAKTERLER gunluk hayatlarini
yasıyor (kosu bandinda kosan biri, sohbet eden aile, bulasik yikayan,
sarj olan telefon, bisiklet, araba). Elektrikli ekipmanlar (priz, powerbank,
Wi-Fi isareti, ekranlar) sahnenin icine dogal olarak yerlestirilmis.

**Ambient mikro-animasyonlar:** Statik degil - pırıltı/sparkle efektleri
(priz yaninda), noktali çizgiler (kablosuz baglanti/hareket izi), yuruyen/
kosan figurler - hepsi hafif dongusel animasyonlarla "canli" bir sahne
hissi veriyor.

**Teknoloji:** Sayfada 2 `<canvas>` elementi var ama belirgin bir
Three.js/GSAP CDN imzasi bulunamadi - buyuk ihtimalle **Lottie**
(After Effects'ten export edilen, canvas/SVG uzerinde oynatilan hafif
vektor animasyon formati) kullaniliyor. Bu, tam da bu tarz "illustrasyon +
kucuk dongusel animasyonlar" isi icin endustri standardi bir tekniktir -
Three.js kadar agir degil, GSAP kadar el-yapimi degil.

## ARK'in Urun Yelpazesi Icin Anlami

Bu format, ARK'in **emlak/arsa portfoyu** ve **çok urunlu katalog**
musterileri icin ayri bir 4. kategori/kullanim senaryosu olarak
degerlendirilebilir:
- Emlak: bir evin/arsanin TUM odalarini/ozelliklerini tek izometrik kesit
  illustrasyonda gostermek (fiziksel fotograf yerine ya da onunla birlikte,
  stilize bir "kesit" gorseli)
- Cok urunlu isletmeler (ör. bir mobilyaci, bir teknoloji marketi): tum
  urun kataloğunu TEK sahnede, her urunu context icinde gosteren bir
  izometrik "magaza kesiti" illustrasyonu

**Teknik yol:** Lottie/vektor illustrasyon + hafif dongusel animasyon,
Three.js/WebGL GEREKMEZ - bu da S+ tier'den cok daha ucuza uretilebilir
demek, ama gorsel etki (kullanicinin "muhtesem otesi" tepkisi) yine de
guclu.

**Kaynak:** https://www2.panasonic.biz/jp/dsr/index/
