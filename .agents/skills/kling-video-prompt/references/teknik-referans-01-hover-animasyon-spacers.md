# Teknik Referans: Hover-Tetiklemeli "Canlanma" Animasyonu (spacers.wannathis.one)

**Ne oldugu:** "Spacers" - indirilebilir bir 3D karakter/illustrasyon setinin
tanitim sayfasi (wannathis.one bir tasarim-asset pazaryeri gibi görünüyor).

**Kullanicinin bu ornegi verme amaci:** "3d bir urun fotografinin uzerine
mouse geldigi an o andan itibaren o 3d fotograf canlanip hareket etmeye
baslamasi" - yani STATIK bir urun/karakter gorseli, fare uzerine gelince
CANLANIP kisa bir hareket dongusune giriyor.

## Dogrulanmis Teknoloji (ONEMLI BULGU)

- **0 canvas elementi** - bu WebGL/Three.js DEGIL
- **jQuery** (`code.jquery.com`) - eski/basit, hafif bir kutuphane
- CloudFront CDN'den asset servisleniyor (`d2pas86kykpvmq.cloudfront.net`)

**Sonuc:** Bu "canlanma" efekti gercek zamanli 3D render DEGIL - buyuk
ihtimalle ONCEDEN URETILMIS bir gorsel/kisa video (veya sprite/GIF) hover
anında oynatiliyor. Iki ekran goruntusu karsilastirildiginda karakterlerin
pozunda (anten egimi, kol pozisyonu) kucuk bir fark gozlemlendi - bu, statik
resmin yerini hover'da kisa bir "idle-loop" videosunun/animasyonun aldigini
dogruluyor.

## ARK Icin Kritik Baglanti: Bu, Kling'in TAM Kullanim Alani

Bu teknik, S+ /7D tier'deki agir Three.js sahnelerinden COK DAHA UCUZ VE
KOLAY uygulanabilir, ve zaten elimizdeki Kling image-to-video prompt
altyapisiyla (bkz. ana `SKILL.md`) birebir orertusuyor:

1. Musterinin urun/karakter FOTOGRAFINI al
2. Kling image-to-video ile kisa bir "idle" hareket dongusu uret (orn. urun
   hafifce donuyor, isik degisiyor - `SKILL.md`'deki "Urun Fotografini
   Canlandirma" sablonuna bak)
3. Sitede: statik gorsel varsayilan olarak durur, `mouseenter`/`hover`
   olayinda uretilen kisa video/gif'e gecis yapilir (CSS `:hover` + video
   swap veya basit bir JS event listener yeterli - Three.js/WebGL GEREKMEZ)

Bu, S2-6/S2-9 vitrin sitelerinde her urun/hizmet karti icin ucuz ve etkili
bir "canlanma" efekti saglar - agir 3D motoru olmadan.

**Kaynak:** https://spacers.wannathis.one/
