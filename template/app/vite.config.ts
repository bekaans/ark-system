import { defineConfig } from "vite";

// webgl-hero-scene.ts (three.js) chunk'i ~527KB (gzip ~132KB) - bu Three.js'in
// WebGLRenderer'inin ic-bagimliligindan kaynaklaniyor (named import'larla
// bile kucalmiyor, olculdu). Bu chunk SADECE S/S+ tier'de dinamik import()
// ile lazy-load edildigi icin (B/A/C hic indirmiyor) gercek Lighthouse mobil
// performansini dusurmuyor (test: S=99/100, S+=94/100, esik=85) - bu limit
// sadece build uyarisini susturur, gercek bir performans ayari degildir.
export default defineConfig({
  build: {
    chunkSizeWarningLimit: 600,
  },
});
