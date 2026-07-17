# ARK Vitrin Sablonu v1 (s2-1)

Vite + vanilla TS + GSAP ScrollTrigger tabanli, `site.config.json` okuyup 5
bolumu (hero, hizmet izgarasi, 2. animasyon, sosyal kanit, iletisim) render
eden sablon motoru.

## Calistirma

```
npm install
npm run dev
```

`public/site.config.json` dosyasi (su an `../site.config.example.json`'un bir
kopyasi) sitenin icerigini besler. Gercek bir isletme icin bu dosyayi
degistirmek yeterli - kod degismiyor.

## Canvas frame-sequence

`src/canvas-frame-sequence.ts`, `hero` ve `animation_2` bolumlerinde kullanilan
scroll-scrubbing animasyon komponenti. `site.config.json`'daki `video_asset`
klasorunde `frame-0001.jpg`, `frame-0002.jpg`, ... bekler (Higgsfield'dan
uretilecek, s2-3/s2-6). Kareler henuz yoksa (404), otomatik olarak renkli bir
placeholder'a duser - scroll-scrubbing mantigi (ScrollTrigger pin+scrub) gercek
kareler olmadan da test edilebilir.

## Durum

- [x] Scroll pozisyonu -> kare cizimi (test edildi: hue degisimi + pinleme
  tarayicida dogrulandi)
- [x] 5 bolum iskeleti config'ten okunuyor
- [ ] Gercek cihaz testi (iPhone + ucuz Android) - kullanicinin kendisi
  yapmali, bu ortamda fiziksel cihaz/emulator erisimi yok
