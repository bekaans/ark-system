"""
ARK - site.config.json icin mini validator (PDF s2-2).

Tam JSON Schema motoru degil, bilerek basit: sadece "required" alanlarin
eksik olup olmadigini kontrol eder ve hangi alanin nerede eksik oldugunu
soyler. Sablon derlenmeden once (Ajan 3) bu script calisir.

Kullanim:
  python validate_config.py site.config.example.json
"""

import json
import sys
from pathlib import Path

REQUIRED = {
    "": ["site_id", "tier", "business", "sections", "seo", "deploy"],
    "business": ["name", "sector_code", "sector_name", "city", "phone"],
    "sections": ["hero", "services_grid", "social_proof", "contact"],
    "sections.hero": ["headline"],
    "sections.services_grid": ["items"],
    "sections.contact": ["cta_text"],
    "seo": ["meta_title", "meta_description", "target_keywords"],
    "deploy": ["subdomain", "status"],
}

# Tier isimleri 2026-07-19'da B/A/S/S+ olarak degistirildi (eski 3D->A, 7D->S,
# hover+pinned_story tier'i S->S+). B tier YENI: Kling video hic uretilmiyor,
# statik/CSS animasyonlu duz site - bkz README.md tier yeniden adlandirma notu.
VALID_TIER = {"B", "A", "S", "S+"}
VALID_STATUS = {"draft", "review", "live"}


def get_nested(config: dict, path: str):
    if path == "":
        return config
    node = config
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def validate(config: dict) -> list[str]:
    errors = []

    for path, fields in REQUIRED.items():
        node = get_nested(config, path)
        if node is None:
            if path != "":
                errors.append(f"eksik nesne: '{path}'")
            continue
        for field in fields:
            if field not in node or node[field] in (None, "", []):
                full = f"{path}.{field}" if path else field
                errors.append(f"eksik/boş alan: '{full}'")

    tier = config.get("tier")
    if tier is not None and tier not in VALID_TIER:
        errors.append(f"gecersiz tier: '{tier}' (beklenen: B, A, S veya S+)")

    status = get_nested(config, "deploy.status") if get_nested(config, "deploy") else None
    if status is not None and status not in VALID_STATUS:
        errors.append(f"gecersiz deploy.status: '{status}' (beklenen: draft/review/live)")

    # B tier: Kling videosu YOK - hero.image zorunlu, video_asset/animation_2 kullanilmaz.
    # A/S/S+ tier: hero.video_asset+frame_count VE sections.animation_2 zorunlu (Kling uretimi).
    hero = get_nested(config, "sections.hero") or {}
    if tier == "B":
        if not hero.get("image"):
            errors.append("B tier icin sections.hero.image zorunlu (video_asset degil)")
    elif tier in ("A", "S", "S+"):
        if not hero.get("video_asset") or not hero.get("frame_count"):
            errors.append(f"{tier} tier icin sections.hero.video_asset ve frame_count zorunlu")
        animation_2 = get_nested(config, "sections.animation_2")
        if animation_2 is None:
            errors.append(f"{tier} tier icin sections.animation_2 zorunlu")
        elif not animation_2.get("video_asset") or not animation_2.get("frame_count"):
            errors.append(f"{tier} tier icin sections.animation_2.video_asset ve frame_count zorunlu")

    # HER tier musterinin KENDI fotograflarini kullanir (2026-07-19 duzeltmesi:
    # sektor-bazli jenerik/stok icerik YOK artik). Fark, o fotograflara ne kadar
    # animasyon/efekt uygulandiginda: B=duz foto, A=kisa Kling girisi,
    # S=tam Kling video hero, S+=S + hover/pinned_story/tum efektler.
    photos = get_nested(config, "media.customer_photos") or []
    if not photos:
        errors.append(f"{tier} tier icin media.customer_photos bos olamaz (artik her tier musteri fotografi kullanir)")

    # S+ tier: S'in ustune hero-hover-pinned_story tam paketi (eski "S").
    if tier == "S+":
        if get_nested(config, "sections.pinned_story") is None:
            errors.append("S+ tier icin sections.pinned_story zorunlu")

    pinned_story = get_nested(config, "sections.pinned_story")
    if pinned_story is not None:
        if not pinned_story.get("wordmark"):
            errors.append("eksik/boş alan: 'sections.pinned_story.wordmark'")
        moments = pinned_story.get("moments") or []
        if len(moments) < 2:
            errors.append("sections.pinned_story.moments en az 2 oge icermeli")
        for i, moment in enumerate(moments):
            if not moment.get("label"):
                errors.append(f"eksik/boş alan: 'sections.pinned_story.moments[{i}].label'")
            if not moment.get("photo"):
                errors.append(f"eksik/boş alan: 'sections.pinned_story.moments[{i}].photo'")

    return errors


def main() -> None:
    if len(sys.argv) < 2:
        print("Kullanim: python validate_config.py <config.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    config = json.loads(path.read_text())
    errors = validate(config)

    if not errors:
        print(f"[ARK] {path.name}: gecerli, eksik alan yok.")
        return

    print(f"[ARK] {path.name}: {len(errors)} sorun bulundu:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)


if __name__ == "__main__":
    main()
