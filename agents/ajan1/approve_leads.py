"""
ARK - Onaylanan flagged lead'leri normal akisa (status='new') geri sokar.

Kullanim:
  python agents/ajan1/approve_leads.py <id_onek1> <id_onek2> ...
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")


def main() -> None:
    if len(sys.argv) < 2:
        print("Kullanim: python approve_leads.py <id_onek1> <id_onek2> ...")
        sys.exit(1)

    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    flagged = supabase.table("leads").select("id,business_id").eq("status", "flagged").execute().data

    approved = 0
    for prefix in sys.argv[1:]:
        matches = [l for l in flagged if l["id"].startswith(prefix)]
        for m in matches:
            supabase.table("leads").update({"status": "new"}).eq("id", m["id"]).execute()
            approved += 1

    print(f"[ARK] {approved} lead onaylanip 'new' durumuna alindi.")


if __name__ == "__main__":
    main()
