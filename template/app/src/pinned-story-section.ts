// ARK - Katalog/Portfoy bolumu (Otsuka-tarzi pin + donen-fotograf + ilerleme-pill)
//
// canvas-frame-sequence.ts ile AYNI GSAP ScrollTrigger pin+scrub mekanizmasini
// kullanir (yeni bir pinleme teknigi degil) - canvas'a kare cizmek yerine,
// pinlenmis konteynerin icinde bir marka/urun adi sabit kalirken, ustune
// binen bir fotograf+anlati+ilerleme-pill katmani scroll ilerledikce
// "moment"ler arasinda crossfade yapar.

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { escapeHtml } from "./sections";

gsap.registerPlugin(ScrollTrigger);

export interface PinnedStoryMoment {
  label: string;
  photo: string;
  narrative?: string;
}

export interface PinnedStoryOptions {
  container: HTMLElement;
  wordmark: string;
  moments: PinnedStoryMoment[];
  pinDuration?: string; // ScrollTrigger "end" degeri, orn. "+=4000"
}

export function createPinnedStorySection(options: PinnedStoryOptions): {
  destroy: () => void;
} {
  const { container, wordmark, moments, pinDuration = "+=4000" } = options;

  container.innerHTML = `
    <div class="ark-story-wordmark">${escapeHtml(wordmark)}</div>
    <div class="ark-story-photo"></div>
    <div class="ark-story-narrative"></div>
    <div class="ark-story-pill"></div>
  `;

  const photoEl = container.querySelector(".ark-story-photo") as HTMLElement;
  const narrativeEl = container.querySelector(".ark-story-narrative") as HTMLElement;
  const pillEl = container.querySelector(".ark-story-pill") as HTMLElement;

  let lastIndex = -1;

  function renderMoment(rawIndex: number) {
    const idx = Math.max(0, Math.min(moments.length - 1, Math.round(rawIndex)));
    if (idx === lastIndex) return;
    lastIndex = idx;
    const moment = moments[idx];
    photoEl.style.opacity = "0";
    window.setTimeout(() => {
      photoEl.style.backgroundImage = `url(${moment.photo})`;
      photoEl.style.opacity = "1";
    }, 200);
    narrativeEl.textContent = moment.narrative ?? "";
    pillEl.textContent = moment.label;
  }

  // DESIGN.md "Do's and Don'ts": reduced-motion tercih edenler icin
  // pin/scrub dayatma - ilk moment'i statik goster (canvas-frame-sequence.ts
  // ile ayni prensip).
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let trigger: ScrollTrigger | null = null;

  renderMoment(0);
  if (!reducedMotion) {
    trigger = ScrollTrigger.create({
      trigger: container,
      start: "top top",
      end: pinDuration,
      pin: true,
      scrub: true,
      onUpdate: (self) => {
        renderMoment(self.progress * (moments.length - 1));
      },
    });
  }

  return {
    destroy() {
      trigger?.kill();
    },
  };
}
