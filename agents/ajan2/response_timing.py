"""
ARK - dm-qualifier adaptif yanit gecikmesi (NLP mirroring/pace-matching).

Musteri ne kadar hizli cevap verirse bot da o kadar hizli cevap vermeye
kayar - last30days arastirmasindaki mirroring bulgusunun (karsi tarafin
ritmini yakala -> bilincalti rapport) dogrudan uygulamasi.

3 kademe (asagi inince bir daha yukari cikilmaz - rapport bozulmasin):
  stage 1: 60-90 sn        (ilk temas / musteri henuz hiz gostermedi)
  stage 2: stage1 gecikmesi - 20 sn   (musteri stage-1 gecikmemizden hizli cevapladi)
  stage 3: 10-15 sn        (musteri stage-2 gecikmemizden de hizli cevapladi)
"""

import os
import random
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

STAGE1_RANGE = (60, 90)
STAGE2_REDUCTION = 20
STAGE3_RANGE = (10, 15)
STAGE2_FLOOR = 15.0  # stage 2, stage 3'un alt sinirinin altina inmesin


def _supabase():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])


def compute_next_delay(
    stage: int,
    last_delay_seconds: Optional[float],
    customer_response_seconds: Optional[float],
) -> tuple[float, int]:
    """
    stage: leads.response_stage (mevcut kademe, 1/2/3)
    last_delay_seconds: bir onceki cevabimizda kullandigimiz gecikme (ilk temasta None)
    customer_response_seconds: musterinin bize cevap verme suresi (henuz yoksa None)

    Donen: (yeni_gecikme_saniye, yeni_stage)
    """
    if last_delay_seconds is None or customer_response_seconds is None:
        return round(random.uniform(*STAGE1_RANGE), 1), 1

    if customer_response_seconds < last_delay_seconds:
        if stage == 1:
            delay = max(last_delay_seconds - STAGE2_REDUCTION, STAGE2_FLOOR)
            return round(delay, 1), 2
        return round(random.uniform(*STAGE3_RANGE), 1), 3

    if stage == 1:
        delay = random.uniform(*STAGE1_RANGE)
    elif stage == 2:
        delay = max(last_delay_seconds, STAGE2_FLOOR)
    else:
        delay = random.uniform(*STAGE3_RANGE)
    return round(delay, 1), stage


def get_state(lead_id: str) -> tuple[int, Optional[float]]:
    supabase = _supabase()
    row = (
        supabase.table("leads")
        .select("response_stage,last_delay_seconds")
        .eq("id", lead_id)
        .single()
        .execute()
        .data
    )
    return row["response_stage"], row.get("last_delay_seconds")


def update_state(lead_id: str, delay_seconds: float, stage: int) -> None:
    supabase = _supabase()
    supabase.table("leads").update(
        {"response_stage": stage, "last_delay_seconds": delay_seconds}
    ).eq("id", lead_id).execute()


def next_delay_for_lead(lead_id: str, customer_response_seconds: Optional[float]) -> float:
    """Bot bir mesaj gondermeden once cagirilir: state'i okur, yeni gecikmeyi
    hesaplar, state'i gunceller ve kac saniye beklenecegini dondurur."""
    stage, last_delay = get_state(lead_id)
    delay, new_stage = compute_next_delay(stage, last_delay, customer_response_seconds)
    update_state(lead_id, delay, new_stage)
    return delay


if __name__ == "__main__":
    # DB'ye dokunmadan mantigi dogrulayan hizli manuel test.
    stage, last_delay = 1, None
    for i, customer_speed in enumerate([None, 45, 12, 8, 30]):
        delay, stage = compute_next_delay(stage, last_delay, customer_speed)
        print(f"adim {i}: musteri_hizi={customer_speed} -> yeni_gecikme={delay}sn, stage={stage}")
        last_delay = delay
