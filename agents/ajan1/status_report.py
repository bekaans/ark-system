"""
ARK - Durum raporu (Bexi'nin ileride yapacagi isin basit/ilk hali).

"Uygunsuz isaretli, onay bekleyen" lead'leri isim+sektor olarak listeler.
Kullanici hangi ID'leri onayladigini soylediginde approve_leads.py ile
status='new' yapilip normal akisa sokulur.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")


def main() -> None:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])

    flagged = (
        supabase.table("leads")
        .select("id,business_id,sector_id,tier")
        .eq("status", "flagged")
        .execute()
        .data
    )

    print(f"\n=== ONAY BEKLEYEN UYGUNSUZ ISARETLI LEAD'LER: {len(flagged)} ===\n")
    for lead in flagged:
        biz = supabase.table("businesses").select("name").eq("id", lead["business_id"]).single().execute().data
        sector = supabase.table("sectors").select("name").eq("id", lead["sector_id"]).single().execute().data
        print(f"[{lead['id'][:8]}] {biz['name']} — {sector['name']} (Tier {lead['tier']})")

    print(f"\nOnaylamak istediklerinin ID'lerini (koseli parantez icindeki kisa kod) soyle.")


if __name__ == "__main__":
    main()
