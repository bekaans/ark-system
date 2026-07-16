"""
ARK - Ajan 1, gorev 10 (tamamlama): dijital gerilik orani + opportunity_score.

Her sektor icin audits tablosundan "zayif site" oranini hesaplar
(animasyonsuz VEYA SEO skoru dusuk), business_volume ile carpip
opportunity_score uretir, sirali ilk 20'yi yazdirir.

CPC adimi (Google Ads) ertelendi - formul bu ikisiyle ilerliyor.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")


def main() -> None:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])

    sectors = supabase.table("sectors").select("id,nace_code,name,business_volume").execute().data

    results = []
    for sector in sectors:
        businesses = (
            supabase.table("businesses").select("id").eq("sector_id", sector["id"]).execute().data
        )
        business_ids = [b["id"] for b in businesses]
        if not business_ids:
            continue

        audits = (
            supabase.table("audits")
            .select("has_animation,seo_score")
            .in_("business_id", business_ids)
            .execute()
            .data
        )
        if not audits:
            continue

        weak_count = sum(1 for a in audits if not a["has_animation"] and (a["seo_score"] or 0) < 60)
        weakness_ratio = weak_count / len(audits)
        volume = sector["business_volume"] or 0
        # basit skor: hacim (normalize, /100) x zayiflik orani x 100
        opportunity_score = round((volume / 100) * weakness_ratio * 100, 1)

        results.append(
            {
                "id": sector["id"],
                "nace_code": sector["nace_code"],
                "name": sector["name"],
                "audited": len(audits),
                "weakness_ratio": round(weakness_ratio, 2),
                "volume": volume,
                "opportunity_score": opportunity_score,
            }
        )

        supabase.table("sectors").update(
            {
                "digital_weakness_ratio": round(weakness_ratio, 2),
                "opportunity_score": opportunity_score,
            }
        ).eq("id", sector["id"]).execute()

    results.sort(key=lambda r: r["opportunity_score"], reverse=True)

    print(f"[ARK] {len(results)} sektor puanlandi. Ilk 20:\n")
    print(f"{'kod':6} {'skor':>6} {'gerilik':>8} {'hacim':>6} {'denetim':>8}  isim")
    for r in results[:20]:
        print(
            f"{r['nace_code']:6} {r['opportunity_score']:>6} {r['weakness_ratio']:>8} "
            f"{r['volume']:>6} {r['audited']:>8}  {r['name']}"
        )


if __name__ == "__main__":
    main()
