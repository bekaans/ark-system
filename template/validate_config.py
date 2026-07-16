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
    "sections": ["hero", "services_grid", "animation_2", "social_proof", "contact"],
    "sections.hero": ["headline", "video_asset", "frame_count"],
    "sections.services_grid": ["items"],
    "sections.animation_2": ["video_asset", "frame_count"],
    "sections.contact": ["cta_text"],
    "seo": ["meta_title", "meta_description", "target_keywords"],
    "deploy": ["subdomain", "status"],
}

VALID_TIER = {"3D", "7D"}
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
        errors.append(f"gecersiz tier: '{tier}' (beklenen: 3D veya 7D)")

    status = get_nested(config, "deploy.status") if get_nested(config, "deploy") else None
    if status is not None and status not in VALID_STATUS:
        errors.append(f"gecersiz deploy.status: '{status}' (beklenen: draft/review/live)")

    if tier == "7D":
        photos = get_nested(config, "media.customer_photos") or []
        if not photos:
            errors.append("7D tier icin media.customer_photos bos olamaz")

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
