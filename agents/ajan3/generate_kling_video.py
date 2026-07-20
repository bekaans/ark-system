"""
ARK - Ajan 3: Kling.ai uzerinden video uretme (text-to-video / image-to-video).

kling_to_frames.py'dan AYRI tutuluyor (tek-sorumluluk): bu script sadece
Kling API'sine istek atip klibi indirir, kare cikarma islemine karismaz.
kling_to_frames.py bu script'in urettigi klibi (veya baska herhangi bir
kaynaktan gelen klibi) girdi olarak kabul eder.

Website urun tier'leri (2026-07-19'da B/A/S/S+ olarak yeniden adlandirildi -
eski 3D/7D isimleri kullanilmiyor). ARTIK HER tier musterinin KENDI
fotografini kullanir (image-to-video, "Subject + Movement" formulu,
kling-video-prompt SKILL.md) - jenerik/sektore-ozel text-to-video YOK
(eski "3D sektor basina bir kez uretilir" kurali KALKTI, cunku artik
jenerik icerik yok). B tier'de Kling hic cagrilmaz (duz foto). A tier
KISA bir klip uretir, S/S+ TAM bir hero klibi uretir - hepsi ayni
image-to-video akisi, sadece sure/kapsam farkli.

text-to-video modu SADECE ARK'in kendi kurumsal sitesi gibi musteri-disi,
soyut/marka icerigi icin kullanilir (bkz.
.agents/skills/kling-video-prompt/references/ark-kurumsal-hero-taslak.md).

Kling API'si ASENKRON: istek gonderilir -> task_id doner -> is bitene
kadar (status=succeed) periyodik sorgulanir -> video_url indirilir.

Kullanim:
  # A/S/S+ tier - musteri fotografindan canlandirma (image-to-video)
  python agents/ajan3/generate_kling_video.py \
    --mode image2video \
    --image musteri-foto.jpg \
    --prompt "Slow dolly push toward the storefront entrance..." \
    --duration 5 \
    --out video.mp4

  # ARK'in kendi sitesi gibi musteri-disi soyut icerik (text-to-video)
  python agents/ajan3/generate_kling_video.py \
    --mode text2video \
    --prompt "Slow dolly push toward a modern car dealership showroom..." \
    --duration 5 \
    --out video.mp4
"""

import argparse
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

# Resmi API host'u global/uluslararasi endpoint - hesap Singapore bolgesindeyse
# KLING_API_BASE=https://api-singapore.klingai.com olarak .env'de override edilebilir.
API_BASE = os.environ.get("KLING_API_BASE", "https://api.klingai.com")
POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 300


def _headers() -> dict:
    api_key = os.environ.get("KLING_API_KEY")
    if not api_key:
        print("[ARK] KLING_API_KEY bulunamadi (litellm/.env icinde olmali).", file=sys.stderr)
        raise SystemExit(1)
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def submit_text_to_video(prompt: str, duration: int, negative_prompt: str | None) -> str:
    payload = {
        "model_name": "kling-v3",
        "prompt": prompt,
        "duration": str(duration),
        "mode": "std",  # std = 720p standart mod (bkz. maliyet notu README'de)
        "aspect_ratio": "16:9",
    }
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt

    resp = requests.post(f"{API_BASE}/v1/videos/text2video", headers=_headers(), json=payload, timeout=30)
    return _extract_task_id(resp)


def submit_image_to_video(image_path: Path, prompt: str, duration: int, negative_prompt: str | None) -> str:
    import base64

    image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    payload = {
        "model_name": "kling-v3",
        "image": image_b64,
        "prompt": prompt,
        "duration": str(duration),
        "mode": "std",
    }
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt

    resp = requests.post(f"{API_BASE}/v1/videos/image2video", headers=_headers(), json=payload, timeout=60)
    return _extract_task_id(resp)


def _extract_task_id(resp: requests.Response) -> str:
    if not resp.ok:
        print(f"[ARK] Kling API hatasi ({resp.status_code}):\n{resp.text}", file=sys.stderr)
        raise SystemExit(1)
    data = resp.json()
    task_id = data.get("data", {}).get("task_id") or data.get("task_id")
    if not task_id:
        print(f"[ARK] Beklenmeyen yanit formati (task_id yok):\n{data}", file=sys.stderr)
        raise SystemExit(1)
    return task_id


def poll_until_done(task_id: str, mode: str) -> str:
    endpoint = f"{API_BASE}/v1/videos/{mode}/{task_id}"
    elapsed = 0
    while elapsed < POLL_TIMEOUT_SECONDS:
        resp = requests.get(endpoint, headers=_headers(), timeout=30)
        if not resp.ok:
            print(f"[ARK] Durum sorgusu hatasi ({resp.status_code}):\n{resp.text}", file=sys.stderr)
            raise SystemExit(1)
        data = resp.json().get("data", {})
        status = data.get("task_status") or data.get("status")
        print(f"[ARK] task {task_id}: {status} ({elapsed}s)")

        if status in ("succeed", "success", "completed"):
            videos = data.get("task_result", {}).get("videos") or data.get("videos")
            if not videos:
                print(f"[ARK] Basarili ama video_url bulunamadi:\n{data}", file=sys.stderr)
                raise SystemExit(1)
            return videos[0]["url"]
        if status in ("failed", "error"):
            print(f"[ARK] Uretim basarisiz:\n{data}", file=sys.stderr)
            raise SystemExit(1)

        time.sleep(POLL_INTERVAL_SECONDS)
        elapsed += POLL_INTERVAL_SECONDS

    print(f"[ARK] Zaman asimi ({POLL_TIMEOUT_SECONDS}s) - task {task_id} hala tamamlanmadi.", file=sys.stderr)
    raise SystemExit(1)


def download(url: str, out: Path) -> None:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    print(f"[ARK] Klip indirildi -> {out} ({len(resp.content) / 1024:.0f} KB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=["text2video", "image2video"])
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative-prompt", default="no warping edges, no jittery motion, no background distortion")
    parser.add_argument("--image", type=Path, help="image2video icin zorunlu - musteri fotografi")
    parser.add_argument("--duration", type=int, default=5, choices=[5, 10])
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    if args.mode == "image2video" and not args.image:
        print("[ARK] --mode image2video icin --image zorunlu.", file=sys.stderr)
        raise SystemExit(1)

    print(f"[ARK] Kling {args.mode} istegi gonderiliyor...")
    if args.mode == "text2video":
        task_id = submit_text_to_video(args.prompt, args.duration, args.negative_prompt)
    else:
        task_id = submit_image_to_video(args.image, args.prompt, args.duration, args.negative_prompt)

    print(f"[ARK] task_id={task_id}, sonuc bekleniyor...")
    video_url = poll_until_done(task_id, args.mode)
    download(video_url, args.out)


if __name__ == "__main__":
    main()
