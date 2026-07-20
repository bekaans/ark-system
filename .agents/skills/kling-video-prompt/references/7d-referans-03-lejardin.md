# 7D Referans #3: lejardin.pha5e.com

**Ne oldugu:** "Phase" (Fransa merkezli "Studio de création digitale" -
dijital yaratim stüdyosu) tarafindan yapilmis "Le Jardin" (Bahce) temali
deneyimsel bir site/demo. Sayfa basligi emoji ile yazilmis: 🌻...🐝.

**Kullanicinin bu ornegi verme amaci (ONEMLI - 7D urununun TAM tarifi):**
Kullanici bunu "gercek isletme fotograflarindan 7D dijital kimlik" konseptinin
somut örneği olarak verdi: "bunun yazılar ile site olmuş hali, o dolaştığı
yerler işletmenin fotoğraflarının video olmuş yerleri gibi" - yani bir
MANAV icin bu tarz bir deneyim yapilsaydi: scroll'da gezilen "arazi" manavin
organik urunleri olur, urun isimleri kalin/animasyonlu font ile yazilir, sag
ust kosede "simdi siparis ver" + adres + telefon gibi isletme bilgileri olur.

## Dogrulanmis Teknoloji

- **8th Wall** - sayfanin en altinda "powered by 8th Wall" ibaresi var. 8th
  Wall, tarayici-ici WebAR/3D deneyimler icin bilinen bir SDK (genelde kamera
  tabanli AR icin kullanilir ama markerless/scroll-tabanli 3D dunyalar icin
  de kullanilabiliyor - burada oyle kullanilmis).
- Sayfa NET OLARAK çok uzun (`body.scrollHeight` ≈ 24,100px) - scroll
  ilerledikce 3D sahnede "ilerleme" hissi bu asiri uzun sayfayla saglaniyor.
- 1 canvas elementi (3D render yuzeyi).

## Gozlemlenen Deneyim (scroll ilerledikce)

1. **Acilis:** Bos, hafif vinyetli krem/bej arka plan, sag ustte muzik
   ikonu (ses acma/kapama)
2. **Ilk bolum (~scroll 1500-4000px):** 3D, cizgi-sanat tarzinda (dis hatlari
   belirgin, duz renkli) bir ARI karakteri havada suzuluyor/donuyor - scroll
   ilerledikce ari farkli acilardan gorunuyor (3D rotasyon)
3. **Orta bolum (~8000px):** Ari, bir ARAZI/TEPE uzerinde ucmaya basliyor -
   wireframe/dokulu bir 3D terrain (toprak + cim dokusu) goruluyor, gercek
   zamanli 3D render oldugu acik (yukleme sirasinda wireframe gorunumu)
4. **~11000px:** Kamera araziye yakinlasiyor, cim/bitki dokusu net gorunuyor,
   ari sahnede ucuyor, ortada stüdyonun kendi logosu "PHA5E - Studio de
   création digitale" yesil/cim dokulu bir yazi tipiyle beliriyor (kendi
   marka tanitimi - musteri projesi olsaydi burada isletme adi/logosu olurdu)

## ARK'in 7D Urunune Uygulama Notu (kullanicinin kendi tarifiyle)

Bu, 7D'nin EN NET tarifi: musterinin gercek fotograflarindan (urunleri,
mekani) turetilmis, scroll'da "icinde gezilen" bir 3D sahne + o sahnenin
icinde YUZEN/ANIMASYONLU kalin baslik tipografisiyle urun/hizmet isimleri +
sag ust kosede sabit duran CTA/iletisim bilgisi katmani (bu ornekte muzik
ikonu, musteri projesinde "Simdi Siparis Ver" + adres + telefon olacak).

**Somut senaryo (kullanicinin verdigi ornek):** Bir manav icin: scroll'da
gezilen 3D sahnede organik urunler (sebze/meyve) donerek/yuzerek gorunur,
her urunun yaninda kalin/etkileyici bir fontla urun adi yazar, sag ustte
sabit "Şimdi Sipariş Ver" butonu + adres + telefon numarasi durur.

**Kaynak:** https://lejardin.pha5e.com/ (Phase ajansinin demo/showcase'i)
