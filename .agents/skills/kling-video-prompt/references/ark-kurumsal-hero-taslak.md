# ARK Kurumsal Site Hero - Kling Prompt Taslagi

**Durum:** Taslak, henuz uretilmedi. Kling API bakiyesi yuklenince calistirilacak
(`agents/ajan3/generate_kling_video.py --mode text2video`), sonra
`agents/ajan3/kling_to_frames.py` ile kare dizisine cevrilip
`template/app/src/canvas-frame-sequence.ts` ile ARK'in kendi kurumsal
sitesinin hero bolumune konulacak. **Musteri sablon motoruna (S+ tier)
dokunmuyor** - bu tek seferlik, ARK'in kendi markasi icin.

## Baglam

Kullanicinin referans verdigi activetheory.net canli incelendi:
- Three.js tabanli, tamamen ozel yazilmis WebGL2 motoru (GSAP/Lenis YOK,
  kendi proprietary render katmanlari var)
- Ana JS bundle 1.75MB, yukleme testinde 30+ saniye `/75` yuzdesinde
  TAKILI kaldi - bu oturumda marseille.laphase5.com'da gordugumuz ayni
  guvenilirlik riski
- Karar: gercek bir WebGL motoru kurmak yerine, zaten kanitlanmis Kling
  video -> kare dizisi -> GSAP scroll-scrub pipeline'i ile AYNI GORSEL
  HISSIYAT taklit edilecek (kod riski sifir, Lighthouse'a dokunmuyor)

Active Theory'nin sitesinde gozlemlenen ve taklit edilecek gorsel dil:
tamamen siyah zemin, merkezden disari yayilan organik/akiskan mavi-camgobegi
parlak "dokunac" (tendril) sekilleri, ic ice gecen daire/mesh parcacik
dokusu, yavas surekli morphing hareket, minimal/futuristik his.

## Prompt (metin-tabanli, musteri fotografi YOK - 3D tier mantigiyla ayni: jenerik/marka-ozel)

```
Shot 1 (0-3s): Pure black void background. A small cluster of thin, glowing
cyan-blue organic tendrils begins to form and pulse gently at the center of
the frame, like bioluminescent light filaments slowly unfurling. Slow dolly
push toward the forming shape.

Shot 2 (3-6s): The tendrils continue to grow and morph outward in a radial,
symmetrical pattern, resembling a slowly blooming mandala of light, with a
fine particle mesh texture visible within the glow. Smooth slow orbit around
the shape, revealing its depth and dimensionality.

Shot 3 (6-9s): The radial light form settles into a stable, softly breathing
pulse. Camera holds steady, then a clean minimal wordmark reading "ARK
INTELLIGENCE LABS" fades in below the shape in thin modern sans-serif
letters. Gentle tilt down to center the wordmark in frame.

cinematic lighting, deep black studio void, volumetric cyan-blue glow,
shallow depth of field, high production value, premium futuristic
atmosphere, subtle film grain
```

**Negative prompt onerisi:** no warping edges, no jittery motion, no harsh
white flashes, no text artifacts, no background clutter, no camera shake

## Notlar / degistirilecek yerler

- Renk paleti su an taslak (siyah + camgobegi-mavi) - ARK'in resmi marka
  renkleri henuz belirlenmedi (`README.md`'de sadece domain/marka tescili
  var, tasarim sistemi yok). Kullanici onaylarsa buradan devam edilir,
  degisirse renk kelimeleri (`cyan-blue` -> istenen renge) degistirilir.
- "ARK INTELLIGENCE LABS" yazisinin gercekten net/okunakli cikip
  cikmayacagi Kling'in metin-render zaafiyeti nedeniyle risklidir (cogu
  video modeli net metin uretmekte zorlanir) - ilk denemede metin bulanik
  cikarsa, wordmark'i VIDEO ICINDE degil, kare-dizisi + HTML/CSS overlay
  olarak (mevcut `pinned-story-section.ts`'deki `.ark-story-wordmark`
  deseniyle ayni yontem) eklemek daha guvenilir bir yedek plandir.
- 3 sahne, toplam ~9sn - Kling `duration` parametresi 5 veya 10 saniye
  kabul ediyor (bkz. `generate_kling_video.py`), o yuzden gercek uretimde
  5sn (kisa, tek "sahne" gibi tek prompt) veya 10sn (yukaridaki 3 sahne
  sigdirilir) secilecek.
