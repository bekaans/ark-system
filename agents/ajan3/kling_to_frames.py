"""
ARK - Ajan 3, ilk adim: Kling videosunu kare-dizisine cevir.

Kling.ai (Higgsfield DEGIL - fiyat karsilastirmasi icin README'deki s2-3
notuna bak) uzerinden uretilen kisa bir klibi (mp4/webm - A/S/S+ tier'de
musterinin kendi fotografindan image-to-video akisiyla gelir, B tier'de
Kling hic kullanilmaz - .agents/skills/kling-video-prompt/SKILL.md)
alip, `template/app/src/canvas-frame-sequence.ts`'in BEKLEDIGI
`frame-0001.jpg, frame-0002.jpg, ...` formatinda bir kare dizisine ceviren
ffmpeg pipeline'i. Motor kodunda HICBIR degisiklik gerekmiyor - sadece
dogru adlandirma + dogru klasore yazmak yeterli.

Kullanim:
  python agents/ajan3/kling_to_frames.py \
    --clip video.mp4 \
    --out template/app/public/assets/hero-frames \
    --config template/site.config.json \
    --section hero

`--fps` varsayilani 20 - ~5-8sn'lik bir Kling klibinden ~100-160 kare
uretir, `canvas-frame-sequence.ts`'in scroll-scrub'i icin yeterince
pürüzsüz. `scale=1280:-1` + jpg kalitesi 80 ZORUNLU tutuluyor - PRODUCT.md
"Lighthouse mobil >=85" siniirini agir kare dosyalariyla kirmamak icin.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def extract_frames(clip: Path, out_dir: Path, fps: int, width: int, quality: int) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame-*.jpg"):
        old.unlink()

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(clip),
        "-vf",
        f"fps={fps},scale={width}:-1",
        "-qscale:v",
        str(quality),
        str(out_dir / "frame-%04d.jpg"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ARK] ffmpeg hatasi:\n{result.stderr}", file=sys.stderr)
        raise SystemExit(1)

    frame_count = len(list(out_dir.glob("frame-*.jpg")))
    if frame_count == 0:
        print("[ARK] Hic kare uretilmedi - klip dosyasini kontrol et.", file=sys.stderr)
        raise SystemExit(1)
    return frame_count


def update_config(config_path: Path, section: str, frames_path: str, frame_count: int) -> None:
    config = json.loads(config_path.read_text())
    sections = config.setdefault("sections", {})
    section_data = sections.setdefault(section, {})
    section_data["video_asset"] = frames_path
    section_data["frame_count"] = frame_count
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clip", required=True, type=Path, help="Kling'den gelen mp4/webm klip")
    parser.add_argument("--out", required=True, type=Path, help="Kare dizisi cikti klasoru")
    parser.add_argument("--config", required=True, type=Path, help="site.config.json yolu")
    parser.add_argument("--section", required=True, choices=["hero", "animation_2"])
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--quality", type=int, default=4, help="ffmpeg -qscale:v (dusuk=yuksek kalite, 2-6 arasi tavsiye edilir)")
    parser.add_argument(
        "--frames-path",
        help="config'e yazilacak video_asset URL yolu (varsayilan: --out'un site.config'e gore goreli hali)",
    )
    args = parser.parse_args()

    if not args.clip.exists():
        print(f"[ARK] Klip bulunamadi: {args.clip}", file=sys.stderr)
        raise SystemExit(1)

    frame_count = extract_frames(args.clip, args.out, args.fps, args.width, args.quality)
    print(f"[ARK] {frame_count} kare uretildi -> {args.out}")

    if args.frames_path:
        frames_path = args.frames_path
    elif "public" in args.out.parts:
        # --out genelde template/app/public/assets/<isim> gibi bir yol -
        # video_asset, Vite'in web-root'u olan public/'e GORELI olmali
        # (orn. "assets/hero-frames/"), "/<isim>/" DEGIL.
        public_idx = args.out.parts.index("public")
        frames_path = "/".join(args.out.parts[public_idx + 1 :]) + "/"
    else:
        frames_path = f"assets/{args.out.name}/"
    update_config(args.config, args.section, frames_path, frame_count)
    print(f"[ARK] {args.config}: sections.{args.section}.frame_count = {frame_count} olarak guncellendi.")


if __name__ == "__main__":
    main()
