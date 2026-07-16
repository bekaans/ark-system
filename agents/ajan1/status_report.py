"""
ARK - Durum raporu (Bexi'nin ileride yapacagi isin basit/ilk hali).

"Uygunsuz isaretli, onay bekleyen" lead'leri isim+sektor olarak listeler.
Kullanici hangi ID'leri onayladigini soylediginde approve_leads.py ile
status='new' yapilip normal akisa sokulur.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")


def get_openrouter_balance() -> str:
    """OpenRouter hesabinin kalan bakiyesini dondurur (yuklenen - harcanan)."""
    try:
        r = requests.get(
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()["data"]
        remaining = data["total_credits"] - data["total_usage"]
        return f"${remaining:.2f} kaldi (yuklenen ${data['total_credits']:.2f}, harcanan ${data['total_usage']:.4f})"
    except Exception as exc:
        return f"kontrol edilemedi ({exc})"


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

    print(f"\n=== OPENROUTER BAKIYE ===")
    print(get_openrouter_balance())


if __name__ == "__main__":
    main()
