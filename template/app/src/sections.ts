// ARK - Bolum iskeleti (PDF s2-1): hero, hizmet izgarasi, 2. animasyon,
// sosyal kanit, iletisim. Her fonksiyon site.config.json'daki ilgili
// bolumu okuyup DOM'a basar.

import type { SiteConfig } from "./config";
import type { PinnedStoryMoment } from "./pinned-story-section";

// gsap (canvas-frame-sequence.ts + pinned-story-section.ts uzerinden) SADECE
// bu iki yardimci fonksiyon cagrildiginda dinamik import() ile yuklenir - B/C
// tier'de bu satirlar hic calismadigindan gsap payload'i o build'lere hic
// inmez (bkz. plan §3, "S = sifir GSAP" iddiasinin kod tarafinda dogru
// olmasi icin gerekli).
async function loadCanvasFrameSequence(container: HTMLElement, framesPath: string, frameCount: number) {
  const { createCanvasFrameSequence } = await import("./canvas-frame-sequence");
  createCanvasFrameSequence({ container, framesPath, frameCount });
}

async function loadPinnedStory(container: HTMLElement, wordmark: string, moments: PinnedStoryMoment[]) {
  const { createPinnedStorySection } = await import("./pinned-story-section");
  createPinnedStorySection({ container, wordmark, moments });
}

function staticHeroMarkup(imagePath: string): string {
  return `<div class="ark-hero-static" style="background-image:url(${escapeHtml(imagePath)})"></div>`;
}

// three.js (webgl-hero-scene.ts uzerinden) SADECE bu fonksiyon cagrildiginda
// dinamik import() ile yuklenir - S/S+ disindaki tier'lerde hic calismaz.
// Dusme sirasi (bkz. plan §2/§4): (1) reduced-motion, (2) webgl2 yok,
// (3) import()/kurulum hatasi, (4) calisma zamani context kaybi - dordu de
// AYNI .ark-hero-static markup'ina duser, yeni CSS kurali gerekmez.
async function loadWebglHero(section: HTMLElement, config: SiteConfig, webglScene: NonNullable<SiteConfig["sections"]["hero"]["webgl_scene"]>) {
  const container = section.querySelector(".ark-hero-webgl") as HTMLElement;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const webgl2Supported = !!document.createElement("canvas").getContext("webgl2");
  if (reducedMotion || !webgl2Supported) {
    container.outerHTML = staticHeroMarkup(webglScene.fallback_image);
    return;
  }

  try {
    const { createWebglHeroScene } = await import("./webgl-hero-scene");
    createWebglHeroScene({
      container,
      preset: webglScene.preset,
      videoAsset: webglScene.video_asset,
      accentColor: webglScene.accent_color ?? config.design?.secondary_color,
      choreographed: config.tier === "S+",
      onContextLost: () => {
        container.outerHTML = staticHeroMarkup(webglScene.fallback_image);
      },
    });
  } catch {
    container.outerHTML = staticHeroMarkup(webglScene.fallback_image);
  }
}

export function renderHero(root: HTMLElement, config: SiteConfig) {
  const hero = config.sections.hero;
  const section = document.createElement("section");
  section.className = "ark-section ark-hero";

  const mediaHtml = hero.webgl_scene
    ? `<div class="ark-hero-webgl"><canvas class="ark-hero-webgl-canvas"></canvas></div>`
    : hero.video_asset
      ? `<div class="ark-hero-frames"></div>`
      : staticHeroMarkup(hero.image ?? "");

  section.innerHTML = `
    ${mediaHtml}
    <div class="ark-hero-copy">
      <h1>${escapeHtml(hero.headline)}</h1>
      ${hero.subheadline ? `<p>${escapeHtml(hero.subheadline)}</p>` : ""}
    </div>
  `;
  root.appendChild(section);

  // B/C tier: Kling videosu yok, sadece statik hero.image + CSS Ken Burns/fade
  // (bkz. style.css .ark-hero-static). A tier: Kling kare-dizisi. S/S+ tier:
  // gercek WebGL sahnesi (bkz. loadWebglHero).
  if (hero.webgl_scene) {
    void loadWebglHero(section, config, hero.webgl_scene);
  } else if (hero.video_asset && hero.frame_count) {
    void loadCanvasFrameSequence(section.querySelector(".ark-hero-frames") as HTMLElement, hero.video_asset, hero.frame_count);
  }
}

export function renderServicesGrid(root: HTMLElement, config: SiteConfig) {
  const section = document.createElement("section");
  section.className = "ark-section ark-services";
  const items = config.sections.services_grid.items
    .map(
      (item) => `
        <div class="ark-service-card">
          ${
            item.photo
              ? `<div class="ark-service-media">
                   <img class="ark-service-photo" src="${escapeHtml(item.photo)}" alt="${escapeHtml(item.title)}" loading="lazy" />
                   ${item.hover_clip ? `<video class="ark-service-clip" src="${escapeHtml(item.hover_clip)}" muted loop playsinline preload="none"></video>` : ""}
                 </div>`
              : ""
          }
          <h3>${escapeHtml(item.title)}</h3>
          ${item.description ? `<p>${escapeHtml(item.description)}</p>` : ""}
        </div>`,
    )
    .join("");
  section.innerHTML = `<div class="ark-services-grid">${items}</div>`;
  root.appendChild(section);

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reducedMotion) {
    section.querySelectorAll<HTMLElement>(".ark-service-media").forEach((media) => {
      const clip = media.querySelector("video") as HTMLVideoElement | null;
      if (!clip) return;
      media.addEventListener("mouseenter", () => {
        clip.currentTime = 0;
        clip.play().catch(() => {});
        media.classList.add("is-playing");
      });
      media.addEventListener("mouseleave", () => {
        clip.pause();
        media.classList.remove("is-playing");
      });
    });
  }
}

export function renderAnimation2(root: HTMLElement, config: SiteConfig) {
  // B tier'de bu bolum hic yok (Kling videosu uretilmiyor) - opsiyonel.
  const animation2 = config.sections.animation_2;
  if (!animation2) return;

  const section = document.createElement("section");
  section.className = "ark-section ark-animation2";
  section.innerHTML = `<div class="ark-animation2-frames"></div>`;
  root.appendChild(section);

  void loadCanvasFrameSequence(section.querySelector(".ark-animation2-frames") as HTMLElement, animation2.video_asset, animation2.frame_count);
}

export function renderSocialProof(root: HTMLElement, config: SiteConfig) {
  const section = document.createElement("section");
  section.className = "ark-section ark-social-proof";
  const testimonials = (config.sections.social_proof.testimonials ?? [])
    .map(
      (t) => `
        <blockquote>
          <p>"${escapeHtml(t.text ?? "")}"</p>
          ${t.author ? `<cite>${escapeHtml(t.author)}</cite>` : ""}
        </blockquote>`,
    )
    .join("");
  section.innerHTML = `<div class="ark-testimonials">${testimonials}</div>`;
  root.appendChild(section);
}

export function renderContact(root: HTMLElement, config: SiteConfig) {
  const section = document.createElement("section");
  section.className = "ark-section ark-contact";
  section.innerHTML = `
    <h2>${escapeHtml(config.sections.contact.cta_text)}</h2>
    ${config.sections.contact.hours ? `<p>${escapeHtml(config.sections.contact.hours)}</p>` : ""}
    <a class="ark-cta-button" href="https://wa.me/${(config.business.whatsapp ?? "").replace(/\D/g, "")}">
      WhatsApp'tan Yaz
    </a>
  `;
  root.appendChild(section);
}

export function renderPinnedStory(root: HTMLElement, config: SiteConfig) {
  const pinnedStory = config.sections.pinned_story;
  if (!pinnedStory) return;

  const section = document.createElement("section");
  section.className = "ark-section ark-pinned-story";
  root.appendChild(section);

  void loadPinnedStory(section, pinnedStory.wordmark, pinnedStory.moments);
}

// C tier: motion-tech butcesi sifir, sabit onceden-uretilmis sablon
// varyanti. Diger tier'lerin hero/services_grid/vb. render fonksiyonlarindan
// TAMAMEN bagimsiz kendi tam sayfa kompozisyonunu kurar - bu yuzden
// renderSite icinde erken bir dal olarak ayriliyor, digerleriyle karismiyor.
const CLASSIC_LAYOUTS = {
  "classic-01": () => import("./layouts/classic-01"),
} as const;

export async function renderSite(root: HTMLElement, config: SiteConfig) {
  document.title = config.seo.meta_title;

  if (config.tier === "C") {
    const key = config.design?.landing_variant ?? "classic-01";
    const loader = CLASSIC_LAYOUTS[key] ?? CLASSIC_LAYOUTS["classic-01"];
    const { renderClassicLanding } = await loader();
    renderClassicLanding(root, config);
    return;
  }

  renderHero(root, config);
  renderServicesGrid(root, config);
  renderAnimation2(root, config);
  renderPinnedStory(root, config);
  renderSocialProof(root, config);
  renderContact(root, config);
}

export function escapeHtml(s: string): string {
  // div.textContent+innerHTML yontemi SADECE &<> kacisini yapar - " ve '
  // kacmadigi icin bu deger bir HTML ATTRIBUTE icine konunca (src="...",
  // style="...") tirnak-kirma/enjeksiyon riski olusuyordu. Manuel replace
  // ile 5 karakterin tamami kaciriliyor (guvenli-kod kural 9).
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
