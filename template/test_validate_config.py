"""
ARK - validate_config.py'daki tier-kosullu kurallar (C/B/A/S/S+) icin
regresyon testleri (2026-07-21).

Harici bagimlilik gerektirmez - sadece validate()'i sentetik config'lerle
cagirir. Yeni bir tier kurali eklenince bu dosya calistirilip mevcut
senaryolarin kirilmadigi dogrulanmali.

Kullanim:
  python template/test_validate_config.py
"""

import copy

from validate_config import validate

BASE: dict = {
    "site_id": "test-site",
    "business": {"name": "Test Isletme", "sector_code": "1.1", "sector_name": "Test", "city": "Test", "phone": "+90500"},
    "sections": {
        "hero": {"headline": "Test basligi"},
        "services_grid": {"items": [{"title": "Hizmet"}]},
        "social_proof": {},
        "contact": {"cta_text": "Yazin"},
    },
    "media": {"customer_photos": ["assets/customer/1.jpg"]},
    "seo": {"meta_title": "T", "meta_description": "D", "target_keywords": ["k"]},
    "deploy": {"subdomain": "test", "status": "draft"},
}


def cfg(**overrides) -> dict:
    c = copy.deepcopy(BASE)
    c["tier"] = overrides.pop("tier")
    for path, value in overrides.items():
        node = c
        parts = path.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return c


WEBGL_SCENE = {"preset": "chrome-ring", "fallback_image": "assets/customer/1.jpg"}
WEBGL_SCENE_VIDEO = {"preset": "video-showcase", "video_asset": "assets/hero-video/clip.mp4", "fallback_image": "assets/customer/1.jpg"}

CASES = [
    # (isim, config, gecerli_mi_bekleniyor)
    ("C gecerli", cfg(tier="C", **{"sections.hero.image": "img.jpg", "design.landing_variant": "classic-01"}), True),
    ("C eksik landing_variant", cfg(tier="C", **{"sections.hero.image": "img.jpg"}), False),
    ("C eksik hero.image", cfg(tier="C", **{"design.landing_variant": "classic-01"}), False),

    ("B gecerli", cfg(tier="B", **{"sections.hero.image": "img.jpg"}), True),
    ("B eksik hero.image", cfg(tier="B"), False),

    (
        "A gecerli",
        cfg(
            tier="A",
            **{
                "sections.hero.video_asset": "assets/hero/",
                "sections.hero.frame_count": 120,
                "sections.animation_2": {"video_asset": "assets/a2/", "frame_count": 90},
            },
        ),
        True,
    ),
    ("A eksik animation_2", cfg(tier="A", **{"sections.hero.video_asset": "assets/hero/", "sections.hero.frame_count": 120}), False),
    ("A eksik video_asset", cfg(tier="A"), False),

    ("S gecerli", cfg(tier="S", **{"sections.hero.webgl_scene": WEBGL_SCENE}), True),
    ("S eksik webgl_scene", cfg(tier="S"), False),
    (
        "S animation_2 kullanilamaz",
        cfg(tier="S", **{"sections.hero.webgl_scene": WEBGL_SCENE, "sections.animation_2": {"video_asset": "a/", "frame_count": 10}}),
        False,
    ),
    (
        "S video_asset kullanilamaz",
        cfg(tier="S", **{"sections.hero.webgl_scene": WEBGL_SCENE, "sections.hero.video_asset": "assets/hero/"}),
        False,
    ),
    ("S video-showcase gecerli", cfg(tier="S", **{"sections.hero.webgl_scene": WEBGL_SCENE_VIDEO}), True),
    (
        "S video-showcase eksik video_asset",
        cfg(tier="S", **{"sections.hero.webgl_scene": {"preset": "video-showcase", "fallback_image": "f.jpg"}}),
        False,
    ),
    (
        "S gecersiz preset",
        cfg(tier="S", **{"sections.hero.webgl_scene": {"preset": "hologram", "fallback_image": "f.jpg"}}),
        False,
    ),

    (
        "S+ gecerli",
        cfg(
            tier="S+",
            **{
                "sections.hero.webgl_scene": WEBGL_SCENE,
                "sections.animation_2": {"video_asset": "a/", "frame_count": 10},
                "sections.pinned_story": {
                    "wordmark": "Marka",
                    "moments": [{"label": "1", "photo": "p1.jpg"}, {"label": "2", "photo": "p2.jpg"}],
                },
            },
        ),
        True,
    ),
    (
        "S+ eksik pinned_story",
        cfg(tier="S+", **{"sections.hero.webgl_scene": WEBGL_SCENE, "sections.animation_2": {"video_asset": "a/", "frame_count": 10}}),
        False,
    ),
    ("S+ eksik animation_2", cfg(tier="S+", **{"sections.hero.webgl_scene": WEBGL_SCENE}), False),
    ("S+ eksik webgl_scene", cfg(tier="S+"), False),

    ("gecersiz tier", cfg(tier="Z"), False),
]


def main() -> None:
    failures = 0
    for name, config, expect_valid in CASES:
        errors = validate(config)
        ok = (not errors) == expect_valid
        failures += 0 if ok else 1
        status = "OK" if ok else "HATA"
        print(f"[{status}] {name} -> {'gecerli' if not errors else errors}")

    print()
    if failures:
        print(f"{failures}/{len(CASES)} test BASARISIZ.")
        raise SystemExit(1)
    print(f"Tum {len(CASES)} test gecti.")


if __name__ == "__main__":
    main()
