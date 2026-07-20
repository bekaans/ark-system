# 7D Referans #1: robinpayot.com

**Ne oldugu:** Robin Payot'nun (Paris merkezli, 2015'ten beri Creative
Developer, kendi WebGL YouTube kanali var) 2022 kisisel portfolyo sitesi.
Awwwards + FWA "Site of the Day" odulu almis. 8 ay bos zamaninda gelistirilmis.

**ARK icin neden onemli:** Bu, "7D" ile hedefledigimiz seyin somut, calisan
bir ornegi - duz bir sayfa degil, scroll ile icinde UCTUGUN bir 3D sahne,
gercek proje gorsellerinin bukulmus/yuzen kartlar olarak bu sahnede yer
almasi. Musteri fotograflarini bu tarz bir deneyime cevirmek 7D'nin ozu.

## Dogrulanmis Teknoloji Yigini

Sitenin JS bundle'i incelendi (`bundle.fc8479f1eef2be9b39d9.js`), asagidaki
imzalar dogrulandi:

- **Three.js** (`WebGLRenderer`, `PerspectiveCamera`, `ShaderMaterial` siniflari
  bulundu) - temel 3D motoru
- **React Three Fiber (r3f)** - Three.js'i React bilesenleri olarak yazmayi
  saglayan katman (Payot'nun Codrops soylesisinde diger projelerinde de
  kullandigini dogruladigi kutuphane)
- **GSAP + ScrollTrigger** - scroll pozisyonunu kamera hareketine/zaman
  cizelgesine baglamak icin
- Kendi ifadesiyle (three.js forumu): "Here is a project I made using
  Three.js in 8 months on my spare time" - shader ve animasyon etiketleriyle
  paylasilmis

## Gozlemlenen Efektler ve Muhtemel Teknik

Tarayiciyla siteye girip scroll ederek dogrudan gozlemlendi (2026-07-18):

### 1. Surekli Kamera Uctan-Uca Hareketi (flythrough)
Scroll ilerledikce kamera bir yol/egri (spline) boyunca ileri hareket ediyor
- sabit bir sayfa kaydirma degil, gercek bir 3D kamera pozisyon/rotasyon
animasyonu. **Muhtemel teknik:** GSAP ScrollTrigger'in `scrub` ozelligiyle
scroll yuzdesi (0-1) bir egri (`THREE.CatmullRomCurve3` gibi) uzerindeki
kamera pozisyonuna map'leniyor - klasik "scroll-driven camera on a spline"
deseni.

### 2. Bukulmus/Yuzen Proje Kartlari
Gercek proje ekran goruntuleri (ornegin "LVMH The Showroom", "Kokopako
portfolio") duz degil, kagit gibi hafif egri bir yuzeye basili gorunuyor.
**Muhtemel teknik:** Duz bir `PlaneGeometry` yerine ozel bir `ShaderMaterial`
(vertex shader'da sinuzoidal/noise tabanli bir egilme/bukulme uygulaniyor)
+ proje ekran goruntusu bir texture olarak bu egri yuzeye map'leniyor.
Bundle'da `ShaderMaterial` sinifi bulunmasi bunu destekliyor.

### 3. Kumlu/Bulanik Dokulu Parcacik Kureler
Degisen boyutlarda, mavi/gri/beyaz tonlarinda, "kum tanesi" gibi dokulu
kureler sahnede sabit/hafif hareketli olarak duruyor, derinlik/atmosfer
hissi veriyor. **Muhtemel teknik:** Kure geometrisi + noise-displaced
vertex shader (yuzeyi pürüzlü/kumlu gostermek icin) veya bir particle/point
sistemi - Payot'nun McDonald's projesinde bahsettigi "Batched Mesh" gibi
performans optimizasyon tekniklerinin burada da kullanilmis olmasi muhtemel.

### 4. Sabit UI Katmani
Sag ustte "ROAD / OVERVIEW / LIST" navigasyonu, sol altta sosyal ikonlar -
bunlar 3D sahnenin USTUNDE duran normal HTML/CSS elemanlari (3D dunyanin
parcasi degil), scroll'dan bagimsiz sabit kalıyor.

## ARK'in 7D Urunune Uygulama Notu

Bu seviyede tam bir Three.js/R3F/GSAP-ScrollTrigger sahnesi kurmak, mevcut
sablon motorumuzun (Vite + GSAP canvas-frame-sequence, bkz.
`template/app/src/canvas-frame-sequence.ts`) kullandigi teknikten **farkli
ve daha karmasik** bir yigin gerektirir - bu bir sonraki asamada (Ajan 3 /
s4-1) degerlendirilecek bir mimari karar. Su an icin bu referans, hem HEDEF
KALITE cizgisini gostermek hem de Kling video prompt'larinda "bu tarz bir
3D-flythrough hissi" istendiginde stil referansi olarak kullanilacak.

**Kaynaklar:**
- Site: https://robinpayot.com/
- Awwwards SOTD: https://www.awwwards.com/sites/robin-payot-portfolio-2022
- Three.js forum (Payot'nun kendi paylasimi): https://discourse.threejs.org/t/portfolio-robin-payot/42559
- Codrops Developer Spotlight (teknik soylesi): https://tympanus.net/codrops/2025/06/12/developer-spotlight-robin-payot/
