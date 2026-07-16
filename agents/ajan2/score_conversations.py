"""
ARK - dm-qualifier sohbet-ici "satisa gecme ihtimali" tier'i (Tier S = satis).

leads.tier (A/B/C) ONCEDEN isletme/firsat degerini olcer - bu script ONA
DOKUNMAZ. Burada hesaplanan leads.sales_tier, sohbet ILERLEDIKCE musterinin
gonderdigi mesajlardaki sinyallere gore guncellenen AYRI bir eksendir:

  S = satis/kapanis sinyali (odeme, IBAN, "anlastik")
  A = randevu/demo/fiyat talebi net
  B = ilgi var ama tereddut/itiraz var
  C = merak/ilk soru asamasi
  D = soguk / henuz sinyal yok

Her tier icin "Tier S'e yukseltmek icin aksiyon" onerisi dondurulur
(last30days NLP arastirmasindaki bulgulara dayanir: reaktivasyon sorusu,
gomulu/dolayli oneri, zayiflatici kelimelerden kacinma).

Kullanim:
  python agents/ajan2/score_conversations.py
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

TIER_SCORE = {"S": 100, "A": 80, "B": 55, "C": 30, "D": 10}

SIGNALS = {
    "S": re.compile(
        r"anla[sş]t[ıi]k|elimi s[ıi]k|ödeme(yi|mi)? (nas[ıi]l|nereye)|"
        r"hesap (numaras[ıi]|bilgisi)|iban|kapora|s[öo]zle[sş]meyi (g[öo]nder|imzala)|"
        r"hemen ba[sş]layal[ıi]m|onayl[ıi]yorum|evet yapal[ıi]m",
        re.IGNORECASE,
    ),
    "A": re.compile(
        r"randevu|g[öo]r[üu][sş]ebilir miyiz|demo|ne zaman (g[öo]r[üu][sş]elim|m[üu]saitsiniz)|"
        r"fiyat[ıi]?n[ıi]z? nedir|teklif (g[öo]nder|alabilir miyim)|toplant[ıi]",
        re.IGNORECASE,
    ),
    "B": re.compile(
        r"d[üu][sş][üu]nece[gğ]im|biraz pahal[ıi]|b[üu]t[çc]e(m)? (yok|uygun de[gğ]il)|"
        r"emin de[gğ]ilim|ba[sş]ka (yerlere )?(de )?bakaca[gğ][ıi]m|acele etmeyelim",
        re.IGNORECASE,
    ),
    "C": re.compile(
        r"nas[ıi]l bir [sş]ey|detay (verir misiniz|alabilir miyim)|"
        r"bilgi (verir misiniz|alabilir miyim)|ilgin[çc]|\?",
        re.IGNORECASE,
    ),
    "D": re.compile(
        r"ilgilenmiyorum|hay[ıi]r te[sş]ekk[üu]r|[sş]u an olmaz|spam|^yok$|^hay[ıi]r$",
        re.IGNORECASE,
    ),
}

ACTION_TO_ESCALATE = {
    "D": "Reaktivasyon sorusu gonder (dusuk baskili, dogrudan): 'Projeden vaz mi gectiniz?' "
         "tarzi bir soru sessiz lead'i yeniden harekete gecirir.",
    "C": "Meragini somut bir bulguya bagla (site zayifligi / rakip ornegi) ve TEK net soru sor; "
         "boylece fiyat konusmasina zemin hazirla.",
    "B": "Itirazi yumusak sekilde yeniden cerceve icine al (fiyati deger/ROI olarak sun), "
         "ardindan acik uclu 'ne zaman uygun' yerine SPESIFIK bir gun/saat oner. Kacamak "
         "cevap ('dusunecegim' gibi) ise sinirli sureli hediye onerilebilir (1 aylik SEO "
         "hediye - scarcity+reciprocity), ama GERCEK ve TESLIM EDILEBILIR olmali.",
    "A": "Somut teklif + randevu/odeme adimini gonder; zorlayici emir yerine gomulu onay "
         "ifadesiyle kapat (orn. 'o zaman basliyoruz').",
    "S": "Kapanisi teyit et, sozlesme/odeme adimini hemen ilerlet, lead.status='won' yap.",
}


def classify_sales_tier(inbound_messages: list[str]) -> tuple[str, float, str]:
    """Musteriden gelen mesajlari en yuksek tier'dan asagiya dogru tarar.
    Ilk eslesen tier kazanir (S en once kontrol edilir)."""
    if not inbound_messages:
        return "D", TIER_SCORE["D"], ACTION_TO_ESCALATE["D"]

    joined = "\n".join(inbound_messages)
    for tier in ("S", "A", "B", "C", "D"):
        if SIGNALS[tier].search(joined):
            return tier, TIER_SCORE[tier], ACTION_TO_ESCALATE[tier]

    # Mesaj var ama hicbir sinyal grubuna girmedi -> notr merak asamasi say.
    return "C", TIER_SCORE["C"], ACTION_TO_ESCALATE["C"]


def main() -> None:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])

    convos = (
        supabase.table("conversations")
        .select("lead_id,direction,message")
        .eq("direction", "inbound")
        .execute()
        .data
    )

    by_lead: dict[str, list[str]] = {}
    for c in convos:
        by_lead.setdefault(c["lead_id"], []).append(c["message"] or "")

    results = []
    for lead_id, messages in by_lead.items():
        tier, score, action = classify_sales_tier(messages)
        supabase.table("leads").update(
            {"sales_tier": tier, "sales_tier_score": score}
        ).eq("id", lead_id).execute()
        results.append((lead_id, tier, score, action))

    if not results:
        print("[ARK] Henuz inbound mesaji olan sohbet yok - siralanacak konusma bulunamadi.")
        print("      (WhatsApp/Chatwoot entegrasyonu tamamlanip ilk yanitlar geldiginde bu script calisir.)")
        return

    results.sort(key=lambda r: r[2], reverse=True)

    print(f"\n=== SOHBETLER - SATISA GECME IHTIMALINE GORE SIRALI (ilk {min(10, len(results))}) ===\n")
    for lead_id, tier, score, action in results[:10]:
        biz = (
            supabase.table("leads")
            .select("business_id")
            .eq("id", lead_id)
            .single()
            .execute()
            .data
        )
        name = (
            supabase.table("businesses")
            .select("name")
            .eq("id", biz["business_id"])
            .single()
            .execute()
            .data["name"]
        )
        print(f"[{lead_id[:8]}] {name} -> Tier {tier} (skor {score})")
        print(f"    Tier S'e yukseltme aksiyonu: {action}\n")


if __name__ == "__main__":
    main()
