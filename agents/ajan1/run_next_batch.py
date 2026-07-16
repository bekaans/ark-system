"""
ARK - s1-7: surekli-calisan dongu ("gecelik" degil, "acik oldugu surece" -
kullanici tercihi). Her calistirmada:

  1. scrape_progress'te bekleyen (sektor, yeni sehir) ciftlerinden kucuk bir
     grup alir (ilk 5 sehir zaten tarandi - CITIES_EXPANSION genisletiliyor)
  2. google-maps-scraper'i SADECE o grup icin calistirir, businesses'e ekler
     (sector.business_volume UZERINE YAZILMAZ, ARTIRILIR)
  3. Henuz denetlenmemis (audits'te kaydi olmayan) birkac siteyi denetler
  4. score_sectors.py + score_leads.py'yi (ikisi de idempotent) yeniden
     calistirir
  5. Islenen ciftleri scrape_progress'te 'done' isaretler

Hata olursa Telegram'a bildirim gonderir (TELEGRAM_BOT_TOKEN/CHAT_ID .env'de
varsa) - sessiz cokme yok.

Kullanim (GitHub Actions veya elle):
  cd ~/ark-system
  python agents/ajan1/run_next_batch.py
"""

import csv
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from sector_terms import SECTOR_TERMS, CITIES, CITIES_EXPANSION  # noqa: E402
from audit_sites import compute_seo_score, detect_tech  # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
SCRAPER_BIN = ROOT / "agents" / "google-maps-scraper" / "google-maps-scraper"
BATCH_SIZE = 10          # her calistirmada en fazla kac (sektor,sehir) cifti islensin
AUDIT_LIMIT = 15         # her calistirmada en fazla kac yeni site denetlensin

ALL_CITIES = CITIES + CITIES_EXPANSION


def _supabase():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])


def notify_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[ARK] Telegram ayarli degil, sadece log'a yaziliyor: {message}")
        return
    import requests

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
    except Exception as exc:
        print(f"[ARK] Telegram bildirimi de basarisiz oldu: {exc}")


def seed_progress(supabase) -> None:
    existing = supabase.table("scrape_progress").select("id").limit(1).execute().data
    if existing:
        return

    print("[ARK] scrape_progress bos - tohumlaniyor.")
    rows = []
    for code in SECTOR_TERMS:
        for city in CITIES:
            rows.append({"sector_code": code, "city": city, "status": "done"})
        for city in CITIES_EXPANSION:
            rows.append({"sector_code": code, "city": city, "status": "pending"})

    batch = 200
    for i in range(0, len(rows), batch):
        supabase.table("scrape_progress").upsert(
            rows[i : i + batch], on_conflict="sector_code,city"
        ).execute()
    print(f"[ARK] {len(rows)} (sektor,sehir) cifti tohumlandi ({len(CITIES)} sehir 'done', {len(CITIES_EXPANSION)} sehir 'pending').")


def get_next_batch(supabase) -> list[dict]:
    return (
        supabase.table("scrape_progress")
        .select("id,sector_code,city")
        .eq("status", "pending")
        .limit(BATCH_SIZE)
        .execute()
        .data
    )


def run_scraper(batch: list[dict]) -> tuple[Path, Path]:
    queries_path = DATA_DIR / "batch_queries.txt"
    results_path = DATA_DIR / "batch_results.csv"
    log_path = DATA_DIR / "batch_scrape.log"

    lines = [f"{SECTOR_TERMS[row['sector_code']]} {row['city']}" for row in batch]
    queries_path.write_text("\n".join(lines) + "\n")

    with open(log_path, "w") as log_f:
        subprocess.run(
            [
                str(SCRAPER_BIN),
                "-input", str(queries_path),
                "-results", str(results_path),
                "-exit-on-inactivity", "1m",  # sinirsiz calismaz - jobler bitip 1dk hareketsiz kalinca cikar
            ],
            stdout=log_f,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=600,
        )
    return log_path, results_path


def import_batch(batch: list[dict], log_path: Path, results_path: Path, supabase) -> None:
    pattern = re.compile(r'Job\{ID: ([0-9a-f-]+), Method: GET, URL: [^,]*/search/([^,]+),')
    jobid_to_code: dict[str, str] = {}
    with open(log_path) as f:
        for line in f:
            m = pattern.search(line)
            if not m:
                continue
            jobid, query = m.group(1), m.group(2).replace("+", " ")
            for city in ALL_CITIES:
                if query.endswith(city):
                    term = query[: -len(city)].strip()
                    code = next((c for c, t in SECTOR_TERMS.items() if t == term), None)
                    if code:
                        jobid_to_code[jobid] = code
                    break

    volume_counter: dict[str, int] = defaultdict(int)
    business_rows = []
    if results_path.exists():
        with open(results_path) as f:
            for row in csv.DictReader(f):
                code = jobid_to_code.get(row["input_id"])
                if not code:
                    continue
                volume_counter[code] += 1
                place_id = row.get("place_id") or row.get("cid")
                if not place_id:
                    continue
                business_rows.append(
                    {
                        "place_id": place_id,
                        "name": row.get("title") or "",
                        "address": row.get("address") or "",
                        "phone": row.get("phone") or None,
                        "website": row.get("website") or None,
                        "_nace_code": code,
                    }
                )

    sectors = supabase.table("sectors").select("id,nace_code,business_volume").execute().data
    code_to_sector = {s["nace_code"]: s for s in sectors}

    for code, count in volume_counter.items():
        sector = code_to_sector.get(code)
        if sector:
            new_volume = (sector["business_volume"] or 0) + count
            supabase.table("sectors").update({"business_volume": new_volume}).eq("id", sector["id"]).execute()

    for b in business_rows:
        sector = code_to_sector.get(b.pop("_nace_code"))
        b["sector_id"] = sector["id"] if sector else None
        supabase.table("businesses").upsert(b, on_conflict="place_id").execute()

    print(f"[ARK] Batch: {len(business_rows)} isletme eklendi/guncellendi, {len(volume_counter)} sektorun hacmi artirildi.")


def audit_new_businesses(supabase) -> None:
    audited_ids = {a["business_id"] for a in supabase.table("audits").select("business_id").execute().data}

    candidates = (
        supabase.table("businesses")
        .select("id,name,website")
        .not_.is_("website", "null")
        .limit(AUDIT_LIMIT * 3)  # audited_ids'e cakisanlari elemek icin fazladan cek
        .execute()
        .data
    )
    todo = [b for b in candidates if b["id"] not in audited_ids][:AUDIT_LIMIT]
    if not todo:
        print("[ARK] Denetlenecek yeni site yok.")
        return

    screenshot_dir = DATA_DIR / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        audited = 0
        for biz in todo:
            try:
                page.goto(biz["website"], timeout=15000, wait_until="domcontentloaded")
                html = page.content()
                tech = detect_tech(html)
                seo = compute_seo_score(html)
                screenshot_path = screenshot_dir / f"{biz['id']}.png"
                page.screenshot(path=str(screenshot_path))
                supabase.table("audits").insert(
                    {
                        "business_id": biz["id"],
                        "has_animation": tech["has_animation"],
                        "has_meta_pixel": tech["has_meta_pixel"],
                        "has_gtag": tech["has_gtag"],
                        "seo_score": seo,
                        "screenshot_url": str(screenshot_path),
                    }
                ).execute()
                audited += 1
            except Exception as exc:
                print(f"[ARK]   denetim hatasi ({biz['name']}): {exc}")
        browser.close()

    print(f"[ARK] {audited} yeni site denetlendi.")


def mark_done(batch: list[dict], supabase) -> None:
    for row in batch:
        supabase.table("scrape_progress").update({"status": "done", "scraped_at": "now()"}).eq(
            "id", row["id"]
        ).execute()


def main() -> None:
    supabase = _supabase()
    try:
        seed_progress(supabase)
        batch = get_next_batch(supabase)

        if not batch:
            print("[ARK] Bekleyen (sektor,sehir) cifti yok - dongu bu calistirmada bosta gecti.")
            return

        print(f"[ARK] Bu calistirmada islenecek {len(batch)} cift: "
              + ", ".join(f"{SECTOR_TERMS[r['sector_code']]}/{r['city']}" for r in batch))

        log_path, results_path = run_scraper(batch)
        import_batch(batch, log_path, results_path, supabase)
        audit_new_businesses(supabase)
        mark_done(batch, supabase)

        subprocess.run([sys.executable, str(Path(__file__).parent / "score_sectors.py")], check=True)
        subprocess.run([sys.executable, str(Path(__file__).parent / "score_leads.py")], check=True)

        print("[ARK] Bu dongu tamamlandi.")
    except Exception as exc:
        notify_telegram(f"[ARK] run_next_batch.py hata verdi: {exc}")
        raise


if __name__ == "__main__":
    main()
