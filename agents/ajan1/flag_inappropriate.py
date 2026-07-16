"""
ARK - Uygunsuz isletmeleri isaretleme.

Isletme adinda belirli anahtar kelimeler (yetiskin urunleri, silah, kumar vb.)
gecen lead'leri status='flagged' yapar. Bu lead'ler kullanici onaylamadan
outreach akisina girmez (draft_outreach.py ve gelecekteki gonderim script'i
sadece status='new' olanlari isler).
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

# Turkce anahtar kelimeler - kaba/hizli bir ilk filtre. Kesin degil,
# kullanicinin onay adimi son karari veriyor.
FLAG_KEYWORDS = [
    r"erotic", r"erotik", r"seks\b", r"sex\b",
    r"silah", r"tabanca", r"tüfek",
    r"kumar", r"bahis", r"casino", r"bet\b",
]
FLAG_PATTERN = re.compile("|".join(FLAG_KEYWORDS), re.IGNORECASE)


def main() -> None:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])

    leads = (
        supabase.table("leads")
        .select("id,business_id,status")
        .eq("status", "new")
        .execute()
        .data
    )
    print(f"[ARK] {len(leads)} 'new' durumundaki lead taranacak.")

    flagged = 0
    for lead in leads:
        biz = supabase.table("businesses").select("name").eq("id", lead["business_id"]).single().execute().data
        if FLAG_PATTERN.search(biz["name"]):
            supabase.table("leads").update({"status": "flagged"}).eq("id", lead["id"]).execute()
            flagged += 1
            print(f"[ARK]   isaretlendi: {biz['name']}")

    print(f"[ARK] Toplam {flagged} lead 'flagged' olarak isaretlendi.")


if __name__ == "__main__":
    main()
