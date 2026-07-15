"""
ARK - Ajan 1, gorev 9: NACE taksonomisini yukle + filtrele.

WorldOfTaxonomy'nin bundled tree-data/nace_rev2.json dosyasindan NACE Rev.2
siniflarini okur, Ajan 1'in LLM zinciriyle (Cerebras -> Gemini -> OpenRouter)
"yerel + tuketiciye donuk + gorsel urunlu" olanlari isaretler, kalanlari
Supabase sectors tablosuna yazar.

Kullanim:
  cd ~/ark-system
  source .venv/bin/activate
  python agents/ajan1/filter_nace.py
"""

import json
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv
from litellm import Router
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

NACE_PATH = ROOT / "agents" / "WorldOfTaxonomy" / "tree-data" / "nace_rev2.json"

import os


def build_router() -> Router:
    with open(ROOT / "litellm" / "config.yaml") as f:
        cfg = yaml.safe_load(f)
    rs = cfg.get("router_settings", {})
    return Router(
        model_list=cfg["model_list"],
        fallbacks=rs.get("fallbacks", []),
        num_retries=rs.get("num_retries", 2),
        timeout=rs.get("timeout", 30),
        cooldown_time=rs.get("cooldown_time", 60),
        allowed_fails=rs.get("allowed_fails", 1),
    )


def load_candidates() -> list[dict]:
    with open(NACE_PATH) as f:
        nace = json.load(f)
    # Seviye 0 (A, B, C...) cok soyut; seviye 1-2 (2-3 haneli) hedef sinifi.
    return [x for x in nace if x["level"] in (1, 2)]


def classify_batch(router: Router, batch: list[dict]) -> list[str]:
    listing = "\n".join(f"{x['code']}: {x['title']}" for x in batch)
    prompt = f"""Asagida NACE Rev.2 sektor siniflari var (kod: baslik).

Gorev: ARK Intelligence adli bir ajans, YEREL, TUKETICIYE DONUK ve GORSEL bir
web sitesinin satis yapmasina yardimci olacagi isletmeleri hedefliyor
(ornek: kuaforler, restoranlar, butik magazalar, spor salonlari, guzellik
salonlari, oto galerileri). B2B/toptan/sanayi/finans/kamu/soyut hizmet
siniflarini (ornek: madencilik, toptan ticaret, sigorta, kamu yonetimi)
HARIC TUT.

Sadece uygun olan kodlarin listesini, virgulle ayrilmis, BASKA HICBIR METIN
OLMADAN don. Ornek format: 47.1,47.2,56.1

Siniflar:
{listing}
"""
    for attempt in range(3):
        response = router.completion(
            model="ajan1-cerebras",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        if content:
            break
        print(f"[ARK] Bos cevap geldi (deneme {attempt + 1}/3), tekrar deneniyor...")
    else:
        raise RuntimeError("3 denemede de bos cevap geldi.")
    codes = [c.strip() for c in re.split(r"[,\n]", content.strip()) if c.strip()]
    return codes


def main() -> None:
    candidates = load_candidates()
    print(f"[ARK] {len(candidates)} aday NACE sinifi yuklendi.")

    router = build_router()

    # Modelin tek seferde cok uzun liste ile hata yapmamasi icin 60'arli batch'lere bol.
    batch_size = 60
    approved_codes: set[str] = set()
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i : i + batch_size]
        print(f"[ARK] Batch {i // batch_size + 1} siniflandiriliyor ({len(batch)} sinif)...")
        codes = classify_batch(router, batch)
        approved_codes.update(codes)

    approved = [x for x in candidates if x["code"] in approved_codes]
    print(f"[ARK] {len(approved)} sinif onaylandi (yerel+tuketici+gorsel).")

    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SECRET_KEY"]
    client = create_client(supabase_url, supabase_key)

    rows = [
        {"nace_code": x["code"], "name": x["title"], "weight": 1.0}
        for x in approved
    ]
    if rows:
        client.table("sectors").upsert(rows, on_conflict="nace_code").execute()
    print(f"[ARK] {len(rows)} sektor 'sectors' tablosuna yazildi.")


if __name__ == "__main__":
    main()
