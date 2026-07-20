"""
ARK - Ajan 1, gorev 14: eski_sistem lead'leri icin ilk mesaj taslaklari.

cold-email skill'inin ilkelerini (akran gibi yaz, kisiselestirme bulguya
baglansin, tek istek, kisa tut) WhatsApp/Instagram DM formatina uyarlayip
Ajan 1'in LLM zinciriyle (Cerebras) taslak uretir.

Once ilk 10 "eski_sistem" (en yuksek firsatli, eski Tier A) lead icin
calisir (checklist kurali: "Ilk 10 mesaji elden gecir - ton senin sesin
olsun").
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from litellm import Router
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

PROMPT_TEMPLATE = """Sen ARK Intelligence Labs adli bir ajans icin WhatsApp/Instagram DM taslagi yaziyorsun.
Ajans, yerel isletmelere modern, animasyonlu web siteleri kuruyor.

Ilkeler (cold-email skill'inden uyarlanmis):
- Akran gibi yaz, satici gibi degil. Bir arkadasin baska bir isletme sahibine
  yazacagi gibi dogal olsun.
- Kisisellestirme MUTLAKA asagidaki spesifik bulguya baglansin - genel/sahte
  kisisellestirme yapma.
- Her cumle bir is yapsin (merak uyandirsin / alakayi kursun / tek soruya goturson).
  Gereksiz hicbir cumle olmasin.
- TEK istek: bir telefon/gorusme randevusu teklif et. Fiyat verme, detaya girme.
- Kisa tut: WhatsApp mesaji, 2-4 cumle, emoji kullanma, resmi olma.
- Turkce yaz, samimi ama profesyonel ton.

KESINLIKLE YASAK (uydurma bilgi - elimizde olmayan hicbir seyi iddia etme):
- Isletme sahibinin/yetkilisinin adini KULLANMA - elimizde bu veri yok, ismi uydurma.
  "Merhaba," veya "Selam," ile basla, kisi adi kullanma.
- "Instagram'inizi takip ediyorum", "sosyal medyada gordum", "sikca ziyaret ediyorum"
  gibi GORMEDIGIN/TAKIP ETMEDIGIN seyleri iddia etme. Tek gercek veri: isletme adi,
  sektoru, ve asagidaki site bulgusu. Sadece bunlara dayan.

Isletme bilgisi:
- Isim: {name}
- Sektor: {sector_name}
- Bulgu: {finding}

Sadece mesaj metnini don, baska hicbir sey yazma (aciklama, basliksiz)."""


def build_router() -> Router:
    with open(ROOT / "litellm" / "config.yaml") as f:
        cfg = yaml.safe_load(f)
    rs = cfg.get("router_settings", {})
    return Router(
        model_list=cfg["model_list"],
        fallbacks=rs.get("fallbacks", []),
        num_retries=rs.get("num_retries", 2),
        timeout=rs.get("timeout", 30),
        cooldown_time=rs.get("cooldown_time", 60),
        allowed_fails=rs.get("allowed_fails", 1),
    )


def describe_finding(audit: dict | None, has_website: bool) -> str:
    if audit is None or not has_website:
        return "isletmenin online gorunur bir websitesi yok"
    if not audit["has_animation"] and (audit["seo_score"] or 0) < 60:
        return "sitesi var ama eski/statik görünüyor, modern animasyon veya güçlü SEO yok"
    return "sitesi temel düzeyde, gelişime açık"


def main() -> None:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    router = build_router()

    leads = (
        supabase.table("leads")
        .select("id,business_id,sector_id")
        .eq("tier", "eski_sistem")
        .is_("outreach_draft", "null")
        .limit(10)
        .execute()
        .data
    )
    print(f"[ARK] {len(leads)} 'eski_sistem' lead icin taslak yazilacak (ilk 10).")

    for lead in leads:
        biz = supabase.table("businesses").select("name,website").eq("id", lead["business_id"]).single().execute().data
        sector = supabase.table("sectors").select("name").eq("id", lead["sector_id"]).single().execute().data
        audit = (
            supabase.table("audits")
            .select("has_animation,seo_score")
            .eq("business_id", lead["business_id"])
            .limit(1)
            .execute()
            .data
        )
        audit = audit[0] if audit else None

        finding = describe_finding(audit, bool(biz["website"]))
        prompt = PROMPT_TEMPLATE.format(name=biz["name"], sector_name=sector["name"], finding=finding)

        response = router.completion(model="ajan1-cerebras", messages=[{"role": "user", "content": prompt}])
        draft = response.choices[0].message.content.strip()

        supabase.table("leads").update({"outreach_draft": draft}).eq("id", lead["id"]).execute()
        print(f"\n--- {biz['name']} ({sector['name']}) ---")
        print(draft)


if __name__ == "__main__":
    main()
