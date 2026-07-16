"""
ARK - Ajan 1, gorev 12: Site denetcisi.

Her sektorden ~30 isletmenin (websitesi olanlar) sitesini Playwright ile
ceker, GSAP/Three.js/Meta Pixel/gtag tespiti yapar, basit bir SEO skoru
cikarir, ekran goruntusu alir. Sonuclari audits tablosuna yazar.

Kullanim:
  cd ~/ark-system
  source .venv/bin/activate
  python agents/ajan1/audit_sites.py
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

SCREENSHOT_DIR = Path(__file__).parent / "data" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

PER_SECTOR_SAMPLE = 30


def compute_seo_score(html: str) -> float:
    score = 0
    checks = [
        bool(re.search(r"<title>[^<]{5,}</title>", html, re.IGNORECASE)),
        bool(re.search(r'<meta[^>]+name=["\']description["\']', html, re.IGNORECASE)),
        bool(re.search(r"<h1[ >]", html, re.IGNORECASE)),
        bool(re.search(r'<meta[^>]+name=["\']viewport["\']', html, re.IGNORECASE)),
        bool(re.search(r'<img[^>]+alt=["\'][^"\']+["\']', html, re.IGNORECASE)),
        bool(re.search(r'rel=["\']canonical["\']', html, re.IGNORECASE)),
    ]
    score = 100 * sum(checks) / len(checks)
    return round(score, 1)


def detect_tech(html: str) -> dict[str, bool]:
    return {
        "has_animation": bool(re.search(r"gsap|three\.min\.js|three\.js", html, re.IGNORECASE)),
        "has_meta_pixel": bool(re.search(r"fbevents\.js|fbq\(", html, re.IGNORECASE)),
        "has_gtag": bool(re.search(r"gtag\(|googletagmanager\.com/gtag", html, re.IGNORECASE)),
    }


def main() -> None:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])

    sectors = supabase.table("sectors").select("id,nace_code,name").execute().data
    print(f"[ARK] {len(sectors)} sektor icin denetim baslatiliyor.")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})  # mobil boyut

        total_audited = 0
        for sector in sectors:
            businesses = (
                supabase.table("businesses")
                .select("id,name,website")
                .eq("sector_id", sector["id"])
                .not_.is_("website", "null")
                .limit(PER_SECTOR_SAMPLE)
                .execute()
                .data
            )
            print(f"[ARK] {sector['nace_code']} ({sector['name']}): {len(businesses)} site denetlenecek.")

            for biz in businesses:
                url = biz["website"]
                try:
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    html = page.content()
                    tech = detect_tech(html)
                    seo = compute_seo_score(html)
                    screenshot_path = SCREENSHOT_DIR / f"{biz['id']}.png"
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
                    total_audited += 1
                except Exception as exc:
                    print(f"[ARK]   HATA ({biz['name']}): {exc}")

        browser.close()

    print(f"[ARK] Toplam {total_audited} site denetlendi, 'audits' tablosuna yazildi.")


if __name__ == "__main__":
    main()
