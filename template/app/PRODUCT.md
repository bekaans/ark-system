# Product

## Register

brand

## Platform

web

## Users

Iki farkli kullanici katmani var. Birincil: yerel Turk isletmesinin (oto
galeri, restoran, otel, kuafor vb.) MUSTERILERI - siteyi ziyaret edip
isletmeyi arayan/WhatsApp'tan yazan/ziyaret eden kisiler, genellikle
telefonda, hizli karar vermek isteyen, sektor hakkinda temel bir fikri olan
ama bu spesifik isletmeyi tanimayan potansiyel musteriler. Ikincil: ARK
Intelligence ekibi - `site.config.json`'u doldurup siteyi devreye alan kisi.

## Product Purpose

Her site, TEK BIR yerel isletme icin uretilen, sektore ozel animasyonlu bir
vitrin (showcase) sitesi. Amac: ziyaretciyi isletmeyle GERCEK bir temasa
(WhatsApp mesaji, telefon arama, fiziksel ziyaret) donusturmek. Basari,
isletmenin "eski/sitesiz" haline kiyasla daha fazla musteri temasi almasidir.

## Positioning

Sektorune ozel, gercek zamanli scroll-animasyonlu bir vitrin - jenerik bir
"kurumsal sablon" degil, o isletmenin kendine ait hissettiren bir deneyim.

## Brand Personality

Guvenilir + modern, ama HER ZAMAN sektore uyarlanabilir olmali - bir oto
galerisi ile bir kuafor salonu ayni "sablon" gibi hissettirmemeli. Sicak,
abartisiz, laf kalabaligi yapmayan. Musterinin gozunde "bu isletme ciddiye
aliniyor" hissi yaratmali.

## Anti-references

Jenerik "AI-yapti sablon" hissi - impeccable'in kendi yasakli listesindeki
kaliplar (gradient text, her bolumde ayni kucuk-harfli "eyebrow" etiket,
cream/sand/bej varsayilan renk paleti, ozdes kart izgaralari, hero-metric
sablonu). Ayrica: genel "kurumsal stok fotograf" hissi - her isletme kendi
sektorune gore FARKLI bir gorsel dil tasimali (site.config.json'daki
design.primary_color/secondary_color + sector_name buna gore uyarlanir).

## Design Principles

- Sektore gore uyarlanabilirlik onceliklidir - tek bir "marka rengi" yok,
  her musteri kendi paletini/hissini tasir.
- Scroll-scrubbing animasyon (canvas frame-sequence) merkezi bir hikaye
  anlatma araci, dekoratif bir efekt degil.
- Telefonda hizli karar veren bir ziyaretci icin tasarla: CTA (WhatsApp) her
  zaman bir kaydirma uzaginda olmali.
- Gercek veriye sadik kal (KESINLIKLE YASAK ilkesi projenin genelinde
  gecerli) - sahte testimonial/istatistik uydurma.
- Performans onceliklidir (Lighthouse mobil >= 85, s2-7 kalite kapisi) -
  gorsel efekt performanstan asla calmaz.

## Accessibility & Inclusion

WCAG AA hedeflenir. Reduced-motion tercih edenler icin scroll-scrubbing
animasyonlarinin crossfade/instant alternatifi olmali (impeccable'in motion
kurali). Kontrast oranlari (govde metni >= 4.5:1) her sektor paleti icin
dogrulanmali.
