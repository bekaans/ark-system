"""
ARK - model_bench.py icin bagimlilik/yapisal duman testi.

Gercek NVIDIA/Groq API cagrisi YAPMAZ (kredi harcamaz) - sadece
litellm/config.yaml'in dogru parse edildigini ve test senaryolarinin
yapisinin bozuk olmadigini dogrular.

Kullanim:
  python agents/ajan-arge/test_model_bench.py
"""

from model_bench import CANDIDATE_MODELS, TEST_CASES, build_router


def test_router_kurulur():
    router = build_router()
    model_names = {m["model_name"] for m in router.model_list}
    assert "dmq-groq" in model_names, f"dmq-groq router'da yok: {model_names}"


def test_senaryolar_dolu():
    assert len(TEST_CASES) >= 1
    for case in TEST_CASES:
        assert case.get("name")
        assert case.get("user")
        assert isinstance(case.get("kontrol_noktalari"), list) and case["kontrol_noktalari"]


def test_aday_modeller_dolu():
    assert len(CANDIDATE_MODELS) >= 1
    assert all(isinstance(m, str) and m for m in CANDIDATE_MODELS)


TESTS = [test_router_kurulur, test_senaryolar_dolu, test_aday_modeller_dolu]


def main() -> None:
    failures = 0
    for test in TESTS:
        try:
            test()
            print(f"[OK] {test.__name__}")
        except Exception as exc:
            failures += 1
            print(f"[HATA] {test.__name__}: {exc}")

    print()
    if failures:
        print(f"{failures}/{len(TESTS)} test BASARISIZ.")
        raise SystemExit(1)
    print(f"Tum {len(TESTS)} test gecti.")


if __name__ == "__main__":
    main()
