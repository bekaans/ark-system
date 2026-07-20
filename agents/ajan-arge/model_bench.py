"""
ARK - Ajan Ar-Ge: NVIDIA NIM uzerinden model kalite karsilastirmasi.

AMAC: Canli musteri trafigine HICBIR ZAMAN dokunmadan, ARK'in gercek
gorevlerini (dm-qualifier sohbet tonu, itiraz karsilama, teshis mesaji)
sabit/sentetik senaryolarla birden fazla modele ayni anda gonderip
cikan cevaplari YAN YANA rapor eder - hangi modelin daha iyi oldugu
KARARI insan (kullanici/Claude Code) tarafindan verilir, otomatik
degildir.

NEDEN SADECE TEST/DEGERLENDIRME: NVIDIA'nin ucretsiz NIM API katmani
(build.nvidia.com, 1000 ucretsiz kredi, kart istemez) KENDI SARTLARINA
GORE sadece "development, testing, research or evaluation" icin -
"activity serving real end-users" (gercek musteri trafigi) production
sayilir ve ayri ucretli NVIDIA AI Enterprise gerektirir. Bu yuzden bu
script SADECE sabit test senaryolariyla calisir, hicbir gercek musteri
verisi/sohbeti bu script'e asla girmez - ToS ihlali riski yok.

Mevcut PRODUKSIYON modeli (dmq-groq, litellm/config.yaml) de karsilastirma
icin AYNI senaryolarla cagrilir - boylece "NVIDIA'daki X modeli, su an
kullandigimiz Groq modelinden gercekten daha mi iyi" sorusuna kanit
tabanli cevap verilir.

Kurulum:
  1. https://build.nvidia.com -> ucretsiz kayit (kart istemez) -> API Key olustur.
  2. litellm/.env'e ekle: NVIDIA_API_KEY=nvapi-...
  3. python agents/ajan-arge/model_bench.py

CIKTI: agents/ajan-arge/reports/<tarih>.md - her senaryo icin her modelin
cevabi yan yana, insan tarafindan okunup karar verilecek sekilde.

NOT (model ID'leri hakkinda): NVIDIA'nin katalogdaki tam model ID string'leri
zaman zaman degisir (Kling.ai'nin model_name'lerinde oldugu gibi ampirik
dogrulama gerekebilir - bkz. agents/ajan3/generate_kling_video.py'deki
benzer sorun). Asagidaki CANDIDATE_MODELS listesi arastirma sirasinda
(2026-07-20) gecerli oldugu bilinen ID'lerle dolduruldu ama ilk gercek
calistirmada 404 alirsan build.nvidia.com/models'tan guncel ID'yi kontrol et.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv
from litellm import Router

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1/chat/completions"

CANDIDATE_MODELS = [
    "meta/llama-3.3-70b-instruct",
    "nvidia/llama-3.3-nemotron-super-49b-v1",
    "deepseek-ai/deepseek-v4-pro",
    "qwen/qwen3-next-80b-a3b-instruct",
]  # 2026-07-20: gercek API cagrilariyla ampirik dogrulandi (hepsi 200 donuyor)

# turkce-nlp-satis-hitabet SKILL.md'nin "Ornek Diyalog" bolumunden alinan
# GERCEK senaryolar (uydurma degil) - kisaltilmis sistem kurallariyla.
SYSTEM_PROMPT = """Sen Kaan'sin, Ark Intelligence'den bir satis danismanisin. WhatsApp
uzerinden Turkce, gundelik, KISA (1-3 cumlelik ayri mesajlar) yaziyorsun.
Kurallar: (1) Once kesif, sonra satis - direkt teklif ATMA. (2) Musterinin
KENDI soyledigi seye dayan, uydurma asinalik/gormedigin seyi iddia etme.
(3) Fiyat sorusu erken gelirse sabit rakam VERME, kopru kur + kesfe don.
(4) Zayiflatici kelimelerden kacin ("sadece", "acaba", "biraz"). (5) Son
cumlede ne "?" ne "." kullanma. (6) Yapay zeka gibi degil, gercek bir
insan gibi yaz - kisa, gundelik, mukemmel noktalama OLMADAN."""

TEST_CASES = [
    {
        "name": "acilis_kesif",
        "user": "(Bu ilk mesaj - musteriden henuz bir sey gelmedi, sen konusmayi acacaksin)",
        "kontrol_noktalari": [
            "Kimlik + kesif sorusu ayri kisa mesajlarda mi",
            "Direkt teklif/pitch var mi (OLMAMALI)",
            "Dogal/gundelik mi, yoksa 'yapay zeka' gibi mi",
        ],
    },
    {
        "name": "erken_fiyat_sorusu",
        "user": "ben Mehmet, fiyati nedir bu arada?",
        "kontrol_noktalari": [
            "Sabit bir TL rakami verildi mi (VERILMEMELI)",
            "Isme gore hitap (Mehmet Bey) kullanildi mi",
            "Kopru kurup kesfe geri donuldu mu",
        ],
    },
    {
        "name": "zayif_site_teshisi",
        "user": (
            "eh iste, gelen geliyor ama pek yeni musteri gelmiyor artik\n"
            "[Kaan siteyi inceledi: animasyon yok, mobilde agir aciliyor]"
        ),
        "kontrol_noktalari": [
            "Musterinin KENDI sikayeti + gozlemlenen bulgu eslestirildi mi",
            "'Siteniz kotu' gibi dogrudan/kaba bir ifade var mi (OLMAMALI)",
            "Uydurma bir gozlem eklendi mi (OLMAMALI - sadece verilen bulgu kullanilmali)",
        ],
    },
]


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


def call_production_model(router: Router, user_message: str) -> str:
    """Su an dm-qualifier'in gercekte kullandigi model (dmq-groq) - karsilastirma
    icin baseline. Router zaten kendi fallback zincirini yonetiyor."""
    resp = router.completion(
        model="dmq-groq",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}],
        max_tokens=300,
    )
    return resp.choices[0].message.content


def call_nvidia_model(model_id: str, user_message: str, api_key: str) -> str:
    resp = requests.post(
        NVIDIA_API_BASE,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model_id,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 300,
            "temperature": 0.7,
        },
        timeout=45,  # bazi modeller (orn. Nemotron) soguk baslangicta yavas cevap veriyor
    )
    if not resp.ok:
        return f"[HATA {resp.status_code}] {resp.text[:200]}"
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def run_benchmark() -> str:
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise SystemExit(
            "[ARK] NVIDIA_API_KEY litellm/.env'de tanimli degil - "
            "bu dosyanin ustundeki 'Kurulum' bolumune bak."
        )

    router = build_router()
    lines = [f"# Model Karsilastirma Raporu - {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    lines.append(
        "> Bu rapor SADECE sabit test senaryolariyla uretildi, hicbir gercek "
        "musteri verisi kullanilmadi. Hangi modelin daha iyi oldugu insan "
        "tarafindan degerlendirilmelidir - otomatik skor YOKTUR."
    )
    lines.append("")

    for case in TEST_CASES:
        lines.append(f"## Senaryo: {case['name']}")
        lines.append(f"**Musteri mesaji:** {case['user']}")
        lines.append("")
        lines.append("**Kontrol noktalari:**")
        for kp in case["kontrol_noktalari"]:
            lines.append(f"- {kp}")
        lines.append("")

        lines.append("### Mevcut produksiyon modeli (dmq-groq)")
        try:
            lines.append(f"> {call_production_model(router, case['user'])}")
        except Exception as exc:
            lines.append(f"> [HATA] {exc}")
        lines.append("")

        for model_id in CANDIDATE_MODELS:
            lines.append(f"### NVIDIA: {model_id}")
            try:
                lines.append(f"> {call_nvidia_model(model_id, case['user'], api_key)}")
            except Exception as exc:
                lines.append(f"> [HATA] {exc}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    report = run_benchmark()
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    out_path = reports_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    out_path.write_text(report)
    print(f"[ARK] Rapor yazildi: {out_path}")


if __name__ == "__main__":
    main()
