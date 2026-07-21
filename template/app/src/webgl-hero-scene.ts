// ARK - S/S+ tier icin gercek WebGL hero sahnesi.
//
// SADECE dinamik import() ile ulasilir (bkz. sections.ts::renderHero) -
// hicbir dosyada statik import edilmez, boylece three.js B/A/C tier
// build'lerine hic girmez (bkz. plan §3).
//
// Iki preset:
// - "video-showcase" (S/S+'in ASIL musteri kullanimi): musterinin GERCEK
//   Kling image-to-video ciktisi (.mp4) VideoTexture ile bir
//   PlaneGeometry'ye dogrudan doku olarak uygulanir - kare cikarma GEREKMEZ.
//   Gercek 3D derinlik/parallax - duz <video>'nun asla veremeyecegi "7D"
//   hissi (kullanicinin kendi tanimi: WebGL'de video 3 boyutlu/dinamik
//   olmali, 2D animasyon o hissi vermiyor).
// - "chrome-ring" (soyut/marka-ozel istisna, ornegin ARK'in kendi sitesi):
//   musteri fotografi olmayan durumlar icin tek geometri + matcap malzeme.
//
// choreographed=false (S tier): kendi requestAnimationFrame donguisunde
// ambient hareket - bu kod yolunda GSAP HIC import edilmez.
// choreographed=true (S+ tier): fonksiyon icinde GSAP/ScrollTrigger dinamik
// import edilip sahne scroll'a baglanir.

// Named import'lar tercih edildi (namespace import * as THREE yerine) -
// dogru/onerilen stil olsa da OLCULDU: bu dosyada gercek chunk boyutunu
// DEGISTIRMEDI (WebGLRenderer'in kendisi zaten cok ic-bagimli, "sadece
// kullandigin sinifi al" mantigi three.js'te calismiyor) - webgl-hero-scene
// chunk'i ~132KB gzip olarak kaliyor. Bu, S/S+ Lighthouse skorunu
// DUSURMEDI (test: 99/100) cunku dinamik import() ile lazy-load ediliyor -
// ilk sayfa yuklemesi/LCP'yi hic etkilemiyor, sadece hero WebGL'e ihtiyac
// duydugunda ayri bir agir istegi olarak gecikmeli cekiliyor.
import {
  AmbientLight,
  Color,
  DirectionalLight,
  Mesh,
  MeshMatcapMaterial,
  MeshPhysicalMaterial,
  PerspectiveCamera,
  PlaneGeometry,
  Scene,
  SRGBColorSpace,
  TorusGeometry,
  VideoTexture,
  WebGLRenderer,
} from "three";

export interface WebglHeroSceneOptions {
  container: HTMLElement; // icinde <canvas class="ark-hero-webgl-canvas"> bulunmali
  preset: "video-showcase" | "chrome-ring";
  videoAsset?: string; // preset=video-showcase icin ZORUNLU
  accentColor?: string;
  choreographed: boolean;
  onContextLost: () => void; // kalici fallback gerektiginde cagrilir (cagiran taraf statige gecer)
}

export interface WebglHeroSceneHandle {
  destroy(): void;
}

const MAX_RESTORE_ATTEMPTS = 2;
const RESTORE_TIMEOUT_MS = 5000;
const RELOAD_FLAG_KEY = "ark_webgl_reload_denendi";

export function createWebglHeroScene(options: WebglHeroSceneOptions): WebglHeroSceneHandle {
  const canvas = options.container.querySelector("canvas");
  if (!canvas) {
    throw new Error("webgl-hero-scene: container icinde <canvas> bulunamadi");
  }

  const renderer = new WebGLRenderer({ canvas, antialias: false, alpha: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.shadowMap.enabled = false;

  const scene = new Scene();
  const camera = new PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.z = 5;

  let videoEl: HTMLVideoElement | null = null;
  let videoTexture: VideoTexture | null = null;
  let mesh: Mesh;

  if (options.preset === "video-showcase") {
    if (!options.videoAsset) {
      throw new Error("webgl-hero-scene: preset=video-showcase icin videoAsset zorunlu");
    }
    videoEl = document.createElement("video");
    videoEl.src = options.videoAsset;
    videoEl.muted = true;
    videoEl.loop = true;
    videoEl.playsInline = true;
    videoEl.preload = "auto";
    void videoEl.play().catch(() => {});

    videoTexture = new VideoTexture(videoEl);
    videoTexture.colorSpace = SRGBColorSpace;
    const geometry = new PlaneGeometry(4, 2.25); // 16:9 - tek duzlem, minimal ucgen sayisi
    const material = new MeshPhysicalMaterial({
      map: videoTexture,
      clearcoat: 0.6,
      clearcoatRoughness: 0.3,
      roughness: 0.4,
      metalness: 0.1,
    });
    mesh = new Mesh(geometry, material);
  } else {
    // chrome-ring: ~8k ucgenin altinda tek geometri, matcap malzeme -
    // gercek zamanli env-map/PBR yansima YOK, ucuz ama parlak gorunum.
    const geometry = new TorusGeometry(1.4, 0.45, 32, 64);
    const material = new MeshMatcapMaterial({ color: new Color(options.accentColor ?? "#ffffff") });
    mesh = new Mesh(geometry, material);
  }

  scene.add(mesh);
  const light = new DirectionalLight(0xffffff, 1);
  light.position.set(2, 2, 3);
  scene.add(light);
  scene.add(new AmbientLight(0xffffff, 0.4));

  function resize() {
    const { clientWidth: w, clientHeight: h } = options.container;
    if (w === 0 || h === 0) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  resize();
  window.addEventListener("resize", resize);

  let rafId = 0;
  let choreographyCleanup: (() => void) | null = null;

  function animate(time: number) {
    if (!options.choreographed) {
      mesh.rotation.y = time * 0.00015;
      mesh.rotation.x = Math.sin(time * 0.0001) * 0.08;
    }
    renderer.render(scene, camera);
    rafId = requestAnimationFrame(animate);
  }

  function startLoop() {
    if (!rafId) rafId = requestAnimationFrame(animate);
  }
  function stopLoop() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = 0;
    }
  }

  // Hero gorunur degilken (scroll disina cikinca) render dongusu durur -
  // pil/performans icin somut onlem, ertelenmeyecek (bkz. plan §2).
  const io = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) startLoop();
      else stopLoop();
    },
    { threshold: 0.01 },
  );
  io.observe(options.container);

  function handleVisibilityChange() {
    if (document.hidden) stopLoop();
    else startLoop();
  }
  document.addEventListener("visibilitychange", handleVisibilityChange);

  // --- webglcontextlost: sinirli (2) denemeli kurtarma + tek seferlik
  // otomatik sayfa yenileme sigortasi (bkz. plan §2) ---
  let restoreAttempts = 0;

  function permanentFallback() {
    stopLoop();
    options.onContextLost();
  }

  function attemptReloadOrFallback() {
    let alreadyReloaded = false;
    try {
      alreadyReloaded = sessionStorage.getItem(RELOAD_FLAG_KEY) === "1";
      if (!alreadyReloaded) sessionStorage.setItem(RELOAD_FLAG_KEY, "1");
    } catch {
      // sessionStorage erisilemiyorsa (gizli mod vb.) yenileme sigortasi
      // guvenilir calismaz - dogrudan kalici fallback'e gec.
      permanentFallback();
      return;
    }
    if (alreadyReloaded) {
      // Bu oturumda zaten bir kez yenilendi ve sorun tekrar olustu -
      // sonsuz yenileme donguisune girmemek icin artik yenileme YOK.
      permanentFallback();
      return;
    }
    window.location.reload();
  }

  function rebuildAfterRestore() {
    // Context kaybinda GPU'daki dokular/buffer'lar geciriz olur - Three.js
    // bir sonraki render() cagrisinda needsUpdate=true isaretli
    // kaynaklari kendiliginden yeniden yukler (renderer'i yeniden
    // olusturmaya gerek yok, ayni canvas/context uzerinde devam eder).
    if (videoTexture) videoTexture.needsUpdate = true;
    mesh.geometry.attributes.position.needsUpdate = true;
    startLoop();
  }

  canvas.addEventListener(
    "webglcontextlost",
    (e) => {
      e.preventDefault(); // tarayicinin context'i geri kurabilmesi icin sart
      stopLoop();

      const timeoutId = window.setTimeout(() => {
        canvas.removeEventListener("webglcontextrestored", onRestored);
        attemptReloadOrFallback();
      }, RESTORE_TIMEOUT_MS);

      function onRestored() {
        window.clearTimeout(timeoutId);
        if (restoreAttempts >= MAX_RESTORE_ATTEMPTS) {
          attemptReloadOrFallback();
          return;
        }
        restoreAttempts += 1;
        rebuildAfterRestore();
      }

      canvas.addEventListener("webglcontextrestored", onRestored, { once: true });
    },
    false,
  );

  async function initChoreography() {
    const gsapModule = await import("gsap");
    const { ScrollTrigger } = await import("gsap/ScrollTrigger");
    gsapModule.default.registerPlugin(ScrollTrigger);
    const trigger = ScrollTrigger.create({
      trigger: options.container,
      start: "top top",
      end: "+=3000",
      scrub: true,
      onUpdate: (self) => {
        mesh.rotation.y = self.progress * Math.PI * 2;
        camera.position.z = 5 - self.progress * 1.5;
      },
    });
    choreographyCleanup = () => trigger.kill();
  }

  if (options.choreographed) {
    void initChoreography();
  }
  startLoop();

  return {
    destroy() {
      stopLoop();
      io.disconnect();
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      choreographyCleanup?.();
      videoEl?.pause();
      videoTexture?.dispose();
      renderer.dispose();
    },
  };
}
