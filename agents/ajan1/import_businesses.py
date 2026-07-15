"""
ARK - Ajan 1, gorev 10 (kismi) + 11: Toplanan isletmeleri Supabase'e aktar,
sektor basina isletme hacmini hesapla.

scrape.log'daki "Job{ID: ..., URL: .../search/{terim}+{sehir}}" satirlarindan
input_id -> arama terimi eslemesi cikarilir, results.csv'deki her satir
buna gore sektore atanir.
"""

import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

DATA_DIR = Path(__file__).parent / "data"
LOG_PATH = DATA_DIR / "scrape.log"
CSV_PATH = DATA_DIR / "results.csv"

from sector_terms import SECTOR_TERMS, CITIES

TERM_TO_CODE = {term: code for code, term in SECTOR_TERMS.items()}


def build_jobid_to_sector() -> dict[str, str]:
    pattern = re.compile(r'Job\{ID: ([0-9a-f-]+), Method: GET, URL: [^,]*/search/([^,]+),')
    jobid_to_code: dict[str, str] = {}
    with open(LOG_PATH) as f:
        for line in f:
            m = pattern.search(line)
            if not m:
                continue
            jobid, query = m.group(1), m.group(2)
            query = query.replace("+", " ")
            for city in CITIES:
                if query.endswith(city):
                    term = query[: -len(city)].strip()
                    code = TERM_TO_CODE.get(term)
                    if code:
                        jobid_to_code[jobid] = code
                    break
    return jobid_to_code


def main() -> None:
    jobid_to_code = build_jobid_to_sector()
    print(f"[ARK] {len(jobid_to_code)} arama gorevi sektore eslendi.")

    volume_counter: dict[str, int] = defaultdict(int)
    business_rows = []
    seen_place_ids = set()

    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = jobid_to_code.get(row["input_id"])
            if not code:
                continue
            volume_counter[code] += 1

            place_id = row.get("place_id") or row.get("cid")
            if not place_id or place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)

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

    print(f"[ARK] {len(business_rows)} tekil isletme (place_id ile), {len(volume_counter)} sektorde bulundu.")

    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])

    sectors = supabase.table("sectors").select("id,nace_code").execute().data
    code_to_id = {s["nace_code"]: s["id"] for s in sectors}

    # 1) business_volume guncelle
    for code, count in volume_counter.items():
        sector_id = code_to_id.get(code)
        if sector_id:
            supabase.table("sectors").update({"business_volume": count}).eq("id", sector_id).execute()
    print(f"[ARK] {len(volume_counter)} sektorun business_volume alani guncellendi.")

    # 2) businesses tablosuna yaz
    rows_to_insert = []
    for b in business_rows:
        sector_id = code_to_id.get(b.pop("_nace_code"))
        b["sector_id"] = sector_id
        # city bilgisi adresten net cikmiyor, city alanini bos birakiyoruz (audits asamasinda tamamlanabilir)
        rows_to_insert.append(b)

    batch_size = 200
    for i in range(0, len(rows_to_insert), batch_size):
        batch = rows_to_insert[i : i + batch_size]
        supabase.table("businesses").upsert(batch, on_conflict="place_id").execute()
    print(f"[ARK] {len(rows_to_insert)} isletme 'businesses' tablosuna yazildi.")


if __name__ == "__main__":
    main()
