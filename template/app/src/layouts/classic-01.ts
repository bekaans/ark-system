// ARK - C tier "classic modern landing" sablon varyanti #1.
//
// C tier'in tum motion-tech butcesi SIFIR (Kling/GSAP/WebGL yok) - bu dosya
// hero/services_grid/animation_2/pinned_story render fonksiyonlarindan
// (../sections.ts) BAGIMSIZ, kendi tam sayfa kompozisyonunu kurar. Diger
// tier'lerden gelen JS/CSS'i asla import etmez, boylece B/A/S/S+ siteleri
// bu dosyanin CSS/JS agirligini hic indirmez (bkz. classic-01.css, sadece
// bu dosyadan import edilir).
//
// Yeni bir varyant (classic-02 vb.) eklemek: impeccable craft/shape/layout
// ile interaktif bir tasarim oturumunda uretilir, config'ten secilmez -
// sections.ts::CLASSIC_LAYOUTS haritasina yeni bir kod-degisikligi girdisi
// olarak eklenir (bkz. plan notu).

import "./classic-01.css";
import type { SiteConfig } from "../config";

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function whatsappHref(rawNumber: string | undefined): string {
  return `https://wa.me/${(rawNumber ?? "").replace(/\D/g, "")}`;
}

export function renderClassicLanding(root: HTMLElement, config: SiteConfig): void {
  const { business, sections } = config;
  const hero = sections.hero;
  const items = sections.services_grid.items;
  const testimonials = sections.social_proof.testimonials ?? [];

  root.innerHTML = `
    <div class="ark-classic">
      <header class="ark-classic-nav">
        <span class="ark-classic-brand">${escapeHtml(business.name)}</span>
        <a class="ark-classic-nav-cta" href="${whatsappHref(business.whatsapp)}">WhatsApp'tan Yaz</a>
      </header>

      <section class="ark-classic-hero">
        <div class="ark-classic-hero-copy">
          <h1>${escapeHtml(hero.headline)}</h1>
          ${hero.subheadline ? `<p>${escapeHtml(hero.subheadline)}</p>` : ""}
          <a class="ark-classic-cta" href="${whatsappHref(business.whatsapp)}">${escapeHtml(sections.contact.cta_text)}</a>
        </div>
        ${
          hero.image
            ? `<div class="ark-classic-hero-photo" style="background-image:url(${escapeHtml(hero.image)})"></div>`
            : ""
        }
      </section>

      <section class="ark-classic-services">
        <div class="ark-classic-services-grid">
          ${items
            .map(
              (item) => `
            <article class="ark-classic-card">
              ${item.photo ? `<img class="ark-classic-card-photo" src="${escapeHtml(item.photo)}" alt="${escapeHtml(item.title)}" loading="lazy" />` : ""}
              <h3>${escapeHtml(item.title)}</h3>
              ${item.description ? `<p>${escapeHtml(item.description)}</p>` : ""}
            </article>`,
            )
            .join("")}
        </div>
      </section>

      ${
        testimonials.length
          ? `<section class="ark-classic-testimonials">
              ${testimonials
                .map(
                  (t) => `
                <blockquote>
                  <p>"${escapeHtml(t.text ?? "")}"</p>
                  ${t.author ? `<cite>${escapeHtml(t.author)}</cite>` : ""}
                </blockquote>`,
                )
                .join("")}
            </section>`
          : ""
      }

      <footer class="ark-classic-contact">
        <h2>${escapeHtml(sections.contact.cta_text)}</h2>
        ${sections.contact.hours ? `<p>${escapeHtml(sections.contact.hours)}</p>` : ""}
        <a class="ark-classic-cta" href="${whatsappHref(business.whatsapp)}">WhatsApp'tan Yaz</a>
      </footer>
    </div>
  `;
}
