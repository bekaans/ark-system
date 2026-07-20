# Otomotiv Sektörü Referans #1: Lusion GEMINI (exp-gemini.lusion.co)

**Ne oldugu:** "Lusion" (taninmis, halen aktif bir Londra merkezli yaratici
teknoloji stüdyosu - Awwwards'ta cok odul kazanmis) tarafindan yapilmis
"GEMINI" adli WebGL araba konfigüratör demosu.

**Kullanicinin degerlendirmesi:** "otomobil sektoru icin ornek alinabilecek
efektleri ve isiklandirmalari iceriyor." **Onemli:** Otomotiv (motor
vehicle sales, NACE 45.1), ARK'in en yuksek kazandiran sektorlerinden biri
(opportunity_score ~251) - bu referans dogrudan en degerli musteri
segmentine hitap ediyor.

## Dogrulanmis Teknoloji

- Tek, kendi sunucusunda barindirilan JS bundle (`exp-gemini.lusion.co`) +
  Google Tag Manager - kutuphane CDN'leri gorunmuyor (muhtemelen hepsi
  bundle icine gomulu)
- **1 canvas, gercek WebGL context dogrulandi** (`getParameter(RENDERER)`
  ile kontrol edildi, "WebKit WebGL" donduruldu - yani gercek zamanli 3D
  render, video degil)
- **Agir yukleme suresi** (~25 saniye) - buyuk ihtimalle yuksek kaliteli
  araba modeli + HDRI/environment map texture'lari (fotogercekci boya/yansima
  icin sart) yukleniyor. ARK icin ders: bu seviye bir deneyimi musteriye
  sunarken yukleme suresi optimizasyonuna (progressive loading, dusuk-poly
  onizleme + arka planda yuksek detay yukleme gibi) onem vermek gerekir.

## Gozlemlenen Deneyim

1. **Acilis:** "GEMINI" logosu koyu degrade arka planda, uzun (agir) bir
   yukleme
2. **Ana sahne:** Konsantrik NEON ISIK HALKALARI (parlak beyaz cizgiler,
   perspektifte tunele benzer bir "isik tuneli" olusturuyor) + yansitici
   (reflective) zemin - dramatik, sinematik bir "araba showroom" atmosferi
3. **Araba modeli:** Fotogercekci, parlak/specular boyali bir spor araba,
   isik halkalarini govdesinde yansitiyor (gercek zamanli reflection/
   specular shading)
4. **INTERAKTIF RENK DEGISTIRME:** Alt kisimda 7 renk secenegi (beyaz,
   siyah, pembe, kirmizi, turuncu, yesil, mavi) - birine tiklayinca araba
   govdesinin boyasi o renge GERCEK ZAMANLI degisiyor. Gecis, on taraftan
   arkaya dogru bir "dalga/wipe" efektiyle ilerliyor (aninda degil,
   kademeli boyanma hissi veriyor - cok etkileyici).
5. Sag ustte "ABOUT" butonu, sol ustte "LUSION:LABS" markasi, "IN MOTION"
   etiketi.

## ARK'in Otomotiv Sektoru Icin Uygulama Notu

Bu, otomotiv/arac satisi musterileri (galeriler, ikinci el arac satisi,
ozel arac modifiye vb.) icin **S+ tier'in somut hedefi**: musterinin
sattigi aracin 3D modelini (ya gercek foto-scan ya da jenerik/stilize bir
3D model) benzer bir "isik tuneli" sahnesinde gosterip, MUSTERININ
sundugu RENK SECENEKLERINI interaktif olarak degistirebilme ozelligi -
bu, "arac galerisi" turu musteriler icin cok guclu bir satis aracı olur
(potansiyel alici aracı istedigi renkte GOREBILIR).

**Teknik yol:** Three.js/WebGL + arac 3D modeli (musteri saglar veya
stok model) + shader-tabanli boya rengi degistirme (material color
uniform) + HDRI/environment map ile gercekci yansima + parcacik/isik
halkasi cevre tasarimi.

**Kaynak:** https://exp-gemini.lusion.co/style
