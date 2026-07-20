# A-Tier Referans #2: kling.ai (resmi site)

**Ne oldugu:** Kling AI'nin kendi resmi tanitim sitesi (Kuaishou). Kullanicinin
kendisi hesap acarken inceledi, "kendi sitesi de cok guzelmis" dedi.

## Dogrulanmis Teknoloji

- **Next.js** (React) - dogrulandi
- **0 canvas, 7 gercek `<video>` elementi** - WebGL/Three.js YOK, hero ve
  ornek gosterimler GERCEK video dosyalari (kendi urettikleri AI klipler)
- GSAP/Lenis imzasi bulunamadi - muhtemelen CSS/Framer-Motion tarzi fade-in
  animasyonlari kullaniliyor, agir bir scroll-kutuphanesi yok

**Sonuc:** controleur.ca gibi, bu da BESPOKE Three.js degil, standart
React + video-arka-plan + CSS animasyonlarla ulasilabilir bir site - bizim
mevcut motorumuza yakin bir eforla tekrar uretilebilir.

## Gozlemlenen Tasarim

### 1. Video Arka Planli Hero + Egik Cizgi Dekoru
Tam ekran gercek video arka plan (arac ici POV surus sahnesi - kendi
urettikleri bir ornek), uzerinde iki ince BEYAZ EGIK CIZGI capraz gecip
sahneyi cerceveliyor (dekoratif "swoosh" efekti). Baslik "All-New KlingAI
3.0 Series" - kalin sans-serif + italik serif karisimi (ujjwalagarwal'da
gordugumuz "iki font stilini karistirma" deseniyle ayni ruh).

### 2. Prompt Seffafligi (ONEMLI, BIZIM ICIN DOGRUDAN UYGULANABILIR)
Hero'nun altinda, o an oynayan ornek videonun **GERCEK PROMPT METNI**
kucuk bir kart icinde gosteriliyor: "In-car POV, handheld shot, focused
on the road ahead." Bu hem urunun yetenegini kanitliyor hem egitici -
ziyaretci "bu videoyu boyle bir prompt'la ürettiler" diye goruyor.

**ARK icin dogrudan uygulama:** Kendi ürettigimiz Kling videolarini
vitrin sitelerinde gosterirken, benzer bir "bu video su prompt'la
uretildi" seffafligi (ozellikle Ajan 3/portfoy sunumlarinda, musteriye
"sizin siteniz icin boyle bir video hazirladik" derken) guven verici bir
teknik olabilir.

### 3. Dikey Zaman-Cizelgesi Ozellik Listesi
Bolum basligi "Kling 3.0 Model Series" (yine kalin+italik karisim).
Solda ince dikey bir çizgiyle baglanmis ozellik listesi (orn. "All-in-One
Reference: Enhanced Consistency...", "Omni Narrative: 15s Multi-Shot
Control...", "Upgraded Native Audio Output...") - her biri scroll ile
aktifleşip/soluklaşıyor, sagda o ozellige ait GERCEK ornek video (bir
kadin kutuphanede kitap okuyor, kamera onune dogru daire ciziyor) + yine
prompt-caption kart formati ("The camera gradually circles to the front
of the... She lifts her head and smiles warmly at the lens.") gorunuyor.

### 4. Genel Stil
Koyu tema, minimal ust navigasyon, "Experience Now"/"Create Now" pill
CTA'lar - teknoloji urunu markalarinda siklikla gorulen "premium/ciddi"
hissi.

## ARK'in Urun Yelpazesi Icin Anlami

Bu, controleur.ca (A-tier) ile ayni kategoride ama daha "teknoloji/premium"
bir estetik hedefleyen musteriler icin (ör. bir yazilim/SaaS sirketi, bir
teknoloji perakendecisi) ikinci bir A-tier referans noktasi. **Prompt-
seffafligi** deseni ozellikle bizim kendi is akisimizla (Kling ile video
uretme) dogrudan orertusuyor - musteri sunumlarinda kullanilabilir.

**Kaynak:** https://kling.ai/
