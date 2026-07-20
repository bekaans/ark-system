"""
ARK - dm-qualifier sohbet-ici "satisa gecme ihtimali" tier'i - GEREKLILIK
TABANLI algoritma (2026-07-19).

(Harf-tabanli S/A/B/C/D isimleri KALKTI - website urun tier'i olan
B/A/S/S+ ile karisiyordu. Artik tanimlayici Turkce isimler kullaniliyor.)

leads.tier (eski_sistem/ortalama/iyi) ONCEDEN isletme/firsat degerini
olcer - bu script ONA DOKUNMAZ. Burada hesaplanan leads.sales_tier, sohbet
ILERLEDIKCE musterinin gonderdigi mesajlardaki sinyallere gore guncellenen
AYRI bir eksendir (dusukten yukseğe):

  sadece_merak          = henuz sinyal yok / soguk (eski "D")
  kararsiz              = merak/ilk soru asamasi (eski "C")
  soguk_satis           = ilgi var ama tereddut/itiraz var (eski "B")
  potansiyel_olabilir   = randevu/demo/fiyat talebi net AMA son-asama
                          gerekliliklerinin hepsi henuz saglanmamis (eski "A")
  potansiyel_musteri    = ASAGIDAKI UC GEREKLILIGIN HEPSI saglandi
                          (VEYA dogrudan kapanis sinyali - odeme/IBAN/"anlastik") (eski "S")

GEREKLILIK MODELI (kullanicinin tanimi): potansiyel_musteri olmak icin
musteri sunlari GOSTERMIS olmali:
  1. sistemi_biliyor   - ne sundugumuzu anladigini gosteren bir yanit verdi
  2. istiyor           - acik bir istek/onay ifadesi kullandi
  3. ariyor_sorunu_var - somut bir ihtiyac/sorun tanimladi, cozum ariyor

Musteri potansiyel_olabilir asamasindaysa (randevu/fiyat/demo istedi) ama bu
3 gerekliligin HEPSI saglanmadiysa, dm-qualifier'in gorevi EKSIK OLANI
COZMEK: sistemi bilmiyorsa ogretir, istek zayifsa NLP ile guclendirir,
somut bir sorun/ihtiyac soylenmediyse bunu sorup ortaya cikarir (bkz.
missing_requirements() ve turkce-nlp-satis-hitabet SKILL.md).

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

TIER_SCORE = {
    "potansiyel_musteri": 100,
    "potansiyel_olabilir": 80,
    "soguk_satis": 55,
    "kararsiz": 30,
    "sadece_merak": 10,
}

# --- Bagimsiz GEREKLILIK sinyalleri (her biri ayri kontrol edilir, tek bir
# "ilk eslesen kazanir" mantigi DEGIL - potansiyel_musteri icin ucu de
# birlikte gerekiyor). ---
REQUIREMENT_SIGNALS = {
    "closing": re.compile(
        r"anla[sş]t[ıi]k|elimi s[ıi]k|ödeme(yi|mi)? (nas[ıi]l|nereye)|"
        r"hesap (numaras[ıi]|bilgisi)|iban|kapora|s[öo]zle[sş]meyi (g[öo]nder|imzala)|"
        r"hemen ba[sş]layal[ıi]m|onayl[ıi]yorum|evet yapal[ıi]m",
        re.IGNORECASE,
    ),
    "appointment_or_price_ask": re.compile(
        r"randevu|g[öo]r[üu][sş]ebilir miyiz|demo|ne zaman (g[öo]r[üu][sş]elim|m[üu]saitsiniz)|"
        r"fiyat[ıi]?n[ıi]z? nedir|teklif (g[öo]nder|alabilir miyim)|toplant[ıi]",
        re.IGNORECASE,
    ),
    "objection": re.compile(
        r"d[üu][sş][üu]nece[gğ]im|biraz pahal[ıi]|b[üu]t[çc]e(m)? (yok|uygun de[gğ]il)|"
        r"emin de[gğ]ilim|ba[sş]ka (yerlere )?(de )?bakaca[gğ][ıi]m|acele etmeyelim",
        re.IGNORECASE,
    ),
    "detail_question": re.compile(
        r"nas[ıi]l bir [sş]ey|detay (verir misiniz|alabilir miyim)|"
        r"bilgi (verir misiniz|alabilir miyim)|ilgin[çc]|\?",
        re.IGNORECASE,
    ),
    "cold": re.compile(
        r"ilgilenmiyorum|hay[ıi]r te[sş]ekk[üu]r|[sş]u an olmaz|spam|^yok$|^hay[ıi]r$",
        re.IGNORECASE | re.MULTILINE,
    ),
    # potansiyel_musteri'nin 3 alt-gerekliligi:
    "sistemi_biliyor": re.compile(
        r"anlad[ıi]m|evet biliyorum|duymu[sş]tum|animasyonlu site|hareketli site|"
        r"canl[ıi] site|scroll|kayd[ıi]rma|nas[ıi]l [çc]al[ıi][sş][ıi]yor.*(anlatt[ıi]n[ıi]z|anlad[ıi]m)",
        re.IGNORECASE,
    ),
    "istiyor": re.compile(
        r"\bistiyorum\b|\byapal[ıi]m\b|\bisterim\b|\bilgileniyorum\b|\bdevam edelim\b|\bbaslayal[ıi]m\b",
        re.IGNORECASE,
    ),
    "ariyor_sorunu_var": re.compile(
        r"sitem.{0,15}(yok|eski|yavas|bozuk)|m[üu][sş]teri.{0,15}(bulam[ıi]yorum|gelmiyor|azald[ıi])|"
        r"g[öo]r[üu]n[üu]r(l[üu])?[üu]k|rakip(lerim)?|ihtiyac[ıi]m var|ariyorum|"
        r"daha once (bir yerlere )?bakt[ıi]m|arastir[ıi]yorum",
        re.IGNORECASE,
    ),
    # bonus/opsiyonel sinyal - hicbir tier kararini TEK BASINA degistirmez,
    # sadece potansiyel_musteri guveninizi guclendirir.
    "had_before": re.compile(
        r"daha once (bir? )?site.*yapt[ıi]r|eskiden.*sitem vard[ıi]|onceki sitem",
        re.IGNORECASE,
    ),
}

FINAL_REQUIREMENTS = ("sistemi_biliyor", "istiyor", "ariyor_sorunu_var")

ACTION_TO_ESCALATE = {
    "sadece_merak": "Reaktivasyon sorusu gonder (dusuk baskili, dogrudan): 'Projeden vaz mi gectiniz?' "
         "tarzi bir soru sessiz lead'i yeniden harekete gecirir.",
    "kararsiz": "Meragini somut bir bulguya bagla (site zayifligi / rakip ornegi) ve TEK net soru sor; "
         "boylece fiyat konusmasina zemin hazirla.",
    "soguk_satis": "Itirazi yumusak sekilde yeniden cerceve icine al (fiyati deger/ROI olarak sun), "
         "ardindan acik uclu 'ne zaman uygun' yerine SPESIFIK bir gun/saat oner. Kacamak "
         "cevap ('dusunecegim' gibi) ise sinirli sureli hediye onerilebilir (1 aylik SEO "
         "hediye - scarcity+reciprocity), ama GERCEK ve TESLIM EDILEBILIR olmali.",
    "potansiyel_musteri": "Kapanisi teyit et, sozlesme/odeme adimini hemen ilerlet, lead.status='won' yap. "
         "1 gun sessiz kalirsa 'karar verebildiniz mi' ile isit; hala olumlu donmezse "
         "soguk_satis asamasindaki ayni hediye (1 aylik SEO 2.0, sinirli sureli) buna da sunulabilir.",
}

# potansiyel_olabilir icin: hangi FINAL_REQUIREMENTS eksikse, o gerekliligi
# HEDEFLEYEN somut aksiyon (kullanicinin "o asamadaki sorunlar cozulur" kurali).
GAP_ACTION = {
    "sistemi_biliyor": "Musteri sistemi tam anlamamis olabilir - TEK cumleyle, jargonsuz "
         "ne yaptigimizi anlat (orn. 'isletmenize ozel, ziyaretcinin ilk 3 saniyede dikkatini "
         "ceken hareketli/animasyonlu bir site hazirliyoruz').",
    "istiyor": "Acik bir istek ifadesi henuz yok - gomulu onay sorusuyla (dogrudan emir degil) "
         "istegi netlestir, orn. 'bu size uygun olur mu' yerine 'o zaman hangi gun baslayalim'.",
    "ariyor_sorunu_var": "Somut bir ihtiyac/sorun soylenmedi - siteyi iste/incele (Adim 2) ve "
         "gozlemlenen zayifligi ONA sorarak dogrulat, boylece kendi agzindan sorunu tanimlamis olsun.",
}


def _detect(joined: str) -> dict[str, bool]:
    return {name: bool(pattern.search(joined)) for name, pattern in REQUIREMENT_SIGNALS.items()}


def missing_requirements(flags: dict[str, bool]) -> list[str]:
    """potansiyel_musteri icin eksik olan gereklilikleri dondurur (bos liste = hepsi tamam)."""
    return [req for req in FINAL_REQUIREMENTS if not flags.get(req)]


def classify_sales_tier(inbound_messages: list[str]) -> tuple[str, float, str]:
    """Musterinin TUM mesajlarindan bagimsiz gereklilik sinyallerini cikarir,
    sonra bu sinyallerin KOMBINASYONUNA gore tier'i belirler (tek bir "ilk
    eslesen kazanir" regex'i DEGIL - potansiyel_musteri icin 3 gerekliligin
    HEPSI ayni anda saglanmali)."""
    if not inbound_messages:
        return "sadece_merak", TIER_SCORE["sadece_merak"], ACTION_TO_ESCALATE["sadece_merak"]

    joined = "\n".join(inbound_messages)
    flags = _detect(joined)

    # 1) Dogrudan kapanis sinyali -> otomatik potansiyel_musteri.
    if flags["closing"]:
        return "potansiyel_musteri", TIER_SCORE["potansiyel_musteri"], ACTION_TO_ESCALATE["potansiyel_musteri"]

    # 2) Randevu/fiyat/demo talebi var mi?
    if flags["appointment_or_price_ask"]:
        gaps = missing_requirements(flags)
        if not gaps:
            # 3 gereklilik de zaten sohbette gecmis -> dogrudan potansiyel_musteri.
            return "potansiyel_musteri", TIER_SCORE["potansiyel_musteri"], ACTION_TO_ESCALATE["potansiyel_musteri"]
        # Eksik var -> potansiyel_olabilir, EKSIK OLANA yonelik somut aksiyon dondur.
        action = " / ".join(GAP_ACTION[g] for g in gaps)
        return "potansiyel_olabilir", TIER_SCORE["potansiyel_olabilir"], action

    # 3) Itiraz/tereddut -> soguk_satis.
    if flags["objection"]:
        return "soguk_satis", TIER_SCORE["soguk_satis"], ACTION_TO_ESCALATE["soguk_satis"]

    # 4) Soguk/ilgisiz -> sadece_merak.
    if flags["cold"]:
        return "sadece_merak", TIER_SCORE["sadece_merak"], ACTION_TO_ESCALATE["sadece_merak"]

    # 5) Detay sorusu / genel merak -> kararsiz.
    if flags["detail_question"]:
        return "kararsiz", TIER_SCORE["kararsiz"], ACTION_TO_ESCALATE["kararsiz"]

    # Mesaj var ama hicbir sinyal grubuna girmedi -> notr kararsiz asamasi say.
    return "kararsiz", TIER_SCORE["kararsiz"], ACTION_TO_ESCALATE["kararsiz"]


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
        print(f"[{lead_id[:8]}] {name} -> {tier} (skor {score})")
        print(f"    Bir sonraki asamaya yukseltme aksiyonu: {action}\n")


if __name__ == "__main__":
    main()
