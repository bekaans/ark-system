# Katalog/Portföy Referans #2: marseille.laphase5.com (3D harita + proje pinleri)

**Ne oldugu:** "La Phase 5" (Fransiz dijital stüdyo - `lejardin.pha5e.com`
ile ayni ajans/domain ailesi olma ihtimali yuksek, "pha5e"/"phase5" ayni
marka) tarafindan yapilmis "Marseille 2021" adli 3D sehir haritasi demosu.

**Kullanicinin tarifi (dogrudan aktarim - ONEMLI, kendi gozlemlerim
sinirli kaldi):** "harita yuklenir, projeler lokasyonlara konulur,
kusbakisi, sectiginin icine girer ve sag ustte tanitim videosu da cikabilir
mesela ekstradan." Emlak veya insaat firmasi icin mukemmel, portfoy icin
uygun.

## Dogrulanmis Teknoloji

- **Three.js** + **OBJLoader2 (v3.2.0)** - console log'da acikca
  dogrulandi ("Using OBJLoader2 version: 3.2.0"). OBJLoader2, Three.js'in
  `.obj` formatinda 3D model/terrain dosyalarini yuklemek icin kullandigi
  resmi eklenti - yani bu, gercek bir 3D sehir/terrain modelinin (Marseille
  sehri) yuklendigini kesin olarak dogruluyor.

## ONEMLI DURUSTLUK NOTU: Yukleme Guvenilirligi Sorunu

Bu siteyi 3 farkli denemede (sayfa yenileme + uzun bekleme, toplamda
~1 dakikayi asan bekleme suresi) tam olarak yukleyemedim - yukleme yuzdesi
%0-27 arasinda takilip kaliyor, konsol hatasi yok ama ilerleme cok
yavas/tutarsiz. Muhtemel sebep: 2021 tarihli bir demo oldugu icin bazi
varliklarin (3D model dosyalari, harita texture'lari) CDN'de bozulmus/
yavaslamis olmasi. **Bu yuzden gorsel dogrulama TAM YAPILAMADI** -
asagidaki tasarim tarifi TAMAMEN kullanicinin kendi tarifine dayanmaktadir,
benim dogrudan gozlemim degildir.

## Kullanicinin Tarifine Gore Deneyim (dogrulanmamis, aktarim)

1. 3D harita/sehir modeli yuklenir (kusbakisi/isometric goruntu)
2. Insaat/emlak PROJELERI, gercek COGRAFI KONUMLARINA (pin/marker olarak)
   yerlestirilmis halde gorunur
3. Kullanici bir proje pinini secince, kamera o lokasyona "girer" (yakinlasma/
   zoom-in animasyonu)
4. Secilen projenin detay goruntusunde, sag ust kosede EKSTRA bir tanitim
   videosu da gosterilebilir (opsiyonel katman)

## ARK'in Urun Yelpazesi Icin Anlami

Bu, emlak/insaat firmalari icin cok GUCLU bir konsept: musterinin TUM
projelerini/portfoyunu TEK bir cografi harita uzerinde, gercek konumlarinda
gostermek - potansiyel alici "bolgede ne var" sorusunu gorsel olarak
cevapliyor. Teknik olarak Three.js + gercek/basitlestirilmis sehir/terrain
modeli + coğrafi koordinat-tabanli pin sistemi gerektiriyor - bu, S+ tier
seviyesinde bir muhendislik yatirimi (robinpayot.com duzeyinde), 20.000 TL+
segmentine uygun. Emlak/arsa portfoyu musterisi gelirse bu somut bir hedef
olarak kullanilabilir, ama yukleme performansi/guvenilirligi konusunda
KENDI UYGULAMAMIZDA cok daha iyi optimize etmemiz gerekecek (bu demo'nun
yasadigi yavaslama sorunu musteri urununde ASLA yasanmamali).

**Kaynak:** https://marseille.laphase5.com/en (yukleme sorunlari nedeniyle
gorsel olarak tam dogrulanamadi, teknik yigin console log'undan
dogrulandi)
