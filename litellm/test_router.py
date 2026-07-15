"""
ARK - LiteLLM router hizli test script'i.

Kullanim:
  cd ~/ark-system/litellm
  source ../.venv/bin/activate
  cp .env.example .env   # sonra .env icine gercek API key'lerini yaz
  python test_router.py ajan1-cerebras "Bu isletme NACE 47.11 sinifina uygun mu? Sadece EVET/HAYIR yaz."

Her agent grubu icin dogru sirada fallback denenir (config.yaml -> router_settings.fallbacks).
Hicbir key girilmemisse veya hepsi rate-limitliyse net bir hata verir, sessizce takilmaz.
"""

import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from litellm import Router

load_dotenv(Path(__file__).parent / ".env")

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def build_router() -> Router:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    rs = cfg.get("router_settings", {})
    return Router(
        model_list=cfg["model_list"],
        fallbacks=rs.get("fallbacks", []),
        num_retries=rs.get("num_retries", 2),
        timeout=rs.get("timeout", 30),
        cooldown_time=rs.get("cooldown_time", 60),
        allowed_fails=rs.get("allowed_fails", 1),
        set_verbose=False,
    )


def main() -> None:
    if len(sys.argv) < 3:
        print("Kullanim: python test_router.py <model-group> <mesaj>")
        print("Ornek gruplar: ajan1-cerebras, dmq-groq, ajan2-gemini, ajan3-openrouter")
        sys.exit(1)

    model_group = sys.argv[1]
    message = " ".join(sys.argv[2:])

    router = build_router()
    print(f"[ARK] '{model_group}' grubuna istek gonderiliyor...")

    try:
        response = router.completion(
            model=model_group,
            messages=[{"role": "user", "content": message}],
        )
        used_model = response.model
        print(f"[ARK] Cevap veren model: {used_model}")
        print("---")
        print(response.choices[0].message.content)
    except Exception as exc:
        print(f"[ARK] HATA: tum zincir (primary + fallback'ler) basarisiz oldu.\n{exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()
