// ARK - Canvas frame-sequence komponenti (PDF s2-1)
//
// Bir klasordeki ardisik kareleri (frame-0001.jpg, frame-0002.jpg, ...) onceden
// yukler, GSAP ScrollTrigger ile scroll pozisyonunu kare indeksine baglar ve
// her scroll adiminda canvas'a ilgili kareyi cizer. Apple urun sayfalarindaki
// "scroll-scrubbing" animasyon efektinin ayni mantigi.

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export interface FrameSequenceOptions {
  container: HTMLElement;
  framesPath: string; // orn. "/assets/hero-frames/" - icinde frame-0001.jpg ... bekleniyor
  frameCount: number;
  framePadding?: number; // dosya adi numara basamak sayisi (varsayilan 4 -> 0001)
  frameExtension?: string; // varsayilan "jpg"
  pinDuration?: string; // ScrollTrigger "end" degeri, orn. "+=3000"
}

export function createCanvasFrameSequence(options: FrameSequenceOptions): {
  destroy: () => void;
} {
  const {
    container,
    framesPath,
    frameCount,
    framePadding = 4,
    frameExtension = "jpg",
    pinDuration = "+=3000",
  } = options;

  const canvas = document.createElement("canvas");
  canvas.className = "frame-sequence-canvas";
  container.appendChild(canvas);
  const ctx = canvas.getContext("2d");

  const images: HTMLImageElement[] = [];
  const frameState = { index: 0 };
  let loadedCount = 0;
  let placeholderMode = false;

  function frameUrl(i: number): string {
    const num = String(i + 1).padStart(framePadding, "0");
    return `${framesPath.replace(/\/$/, "")}/frame-${num}.${frameExtension}`;
  }

  function resizeCanvas() {
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    render();
  }

  function drawPlaceholder(i: number) {
    if (!ctx) return;
    const hue = Math.round((i / Math.max(frameCount - 1, 1)) * 300);
    ctx.fillStyle = `hsl(${hue}, 70%, 45%)`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "rgba(255,255,255,0.85)";
    ctx.font = `${Math.max(canvas.width * 0.04, 16)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(
      `frame ${i + 1}/${frameCount} (placeholder - Higgsfield karesi bekleniyor)`,
      canvas.width / 2,
      canvas.height / 2,
    );
  }

  function render() {
    if (!ctx) return;
    const i = Math.max(0, Math.min(frameCount - 1, Math.round(frameState.index)));
    if (placeholderMode || !images[i] || !images[i].complete || images[i].naturalWidth === 0) {
      drawPlaceholder(i);
      return;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(images[i], 0, 0, canvas.width, canvas.height);
  }

  // Kareleri onceden yukle. Herhangi biri 404 verirse (gercek Higgsfield
  // kareleri henuz uretilmediyse) placeholder moduna dus - sessizce cokme.
  for (let i = 0; i < frameCount; i++) {
    const img = new Image();
    img.onload = () => {
      loadedCount++;
      if (i === frameState.index) render();
    };
    img.onerror = () => {
      placeholderMode = true;
      if (i === frameState.index) render();
    };
    img.src = frameUrl(i);
    images.push(img);
  }

  // DESIGN.md "Do's and Don'ts": reduced-motion tercih eden ziyaretciye
  // scroll-scrubbing dayatma - tek bir statik (ortadaki) kare goster.
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let trigger: ScrollTrigger | null = null;

  if (reducedMotion) {
    frameState.index = Math.floor((frameCount - 1) / 2);
  } else {
    trigger = ScrollTrigger.create({
      trigger: container,
      start: "top top",
      end: pinDuration,
      pin: true,
      scrub: true,
      onUpdate: (self) => {
        frameState.index = self.progress * (frameCount - 1);
        render();
      },
    });
  }

  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();

  return {
    destroy() {
      trigger?.kill();
      window.removeEventListener("resize", resizeCanvas);
      canvas.remove();
    },
  };
}
