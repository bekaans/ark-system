// ARK - Bolum iskeleti (PDF s2-1): hero, hizmet izgarasi, 2. animasyon,
// sosyal kanit, iletisim. Her fonksiyon site.config.json'daki ilgili
// bolumu okuyup DOM'a basar.

import type { SiteConfig } from "./config";
import { createCanvasFrameSequence } from "./canvas-frame-sequence";

export function renderHero(root: HTMLElement, config: SiteConfig) {
  const section = document.createElement("section");
  section.className = "ark-section ark-hero";
  section.innerHTML = `
    <div class="ark-hero-frames"></div>
    <div class="ark-hero-copy">
      <h1>${escapeHtml(config.sections.hero.headline)}</h1>
      ${config.sections.hero.subheadline ? `<p>${escapeHtml(config.sections.hero.subheadline)}</p>` : ""}
    </div>
  `;
  root.appendChild(section);

  createCanvasFrameSequence({
    container: section.querySelector(".ark-hero-frames") as HTMLElement,
    framesPath: config.sections.hero.video_asset,
    frameCount: config.sections.hero.frame_count,
  });
}

export function renderServicesGrid(root: HTMLElement, config: SiteConfig) {
  const section = document.createElement("section");
  section.className = "ark-section ark-services";
  const items = config.sections.services_grid.items
    .map(
      (item) => `
        <div class="ark-service-card">
          <h3>${escapeHtml(item.title)}</h3>
          ${item.description ? `<p>${escapeHtml(item.description)}</p>` : ""}
        </div>`,
    )
    .join("");
  section.innerHTML = `<div class="ark-services-grid">${items}</div>`;
  root.appendChild(section);
}

export function renderAnimation2(root: HTMLElement, config: SiteConfig) {
  const section = document.createElement("section");
  section.className = "ark-section ark-animation2";
  section.innerHTML = `<div class="ark-animation2-frames"></div>`;
  root.appendChild(section);

  createCanvasFrameSequence({
    container: section.querySelector(".ark-animation2-frames") as HTMLElement,
    framesPath: config.sections.animation_2.video_asset,
    frameCount: config.sections.animation_2.frame_count,
  });
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

export function renderSite(root: HTMLElement, config: SiteConfig) {
  document.title = config.seo.meta_title;
  renderHero(root, config);
  renderServicesGrid(root, config);
  renderAnimation2(root, config);
  renderSocialProof(root, config);
  renderContact(root, config);
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}
