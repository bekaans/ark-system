#!/usr/bin/env python3
"""ARK - surekli guvenlik/bug taramasi (2026-07-24, Kaan'in talebi).

BAGIMSIZ CALISIR - Claude Code KULLANMAZ, hicbir Claude usage'i harcamaz.
Yeni bir commit main'e ulastiginda (kendi push'lari + GitHub Actions'in attigi
commit'ler dahil) o commit'in diff'ini `codex exec review --commit <sha>` ile
tarar - Kaan'in ChatGPT girisiyle, ucretsiz. Sorun bulursa Telegram'a hangi
ajanin/dosyanin sorunlu oldugunu yazar ("duzeltilmeyi bekliyor"). Kaan
Telegram'da gorup Claude Code'a donup birlikte cozer.

"Sonsuz siki donen" degil - INTERVAL_SECONDS'ta bir uyuyup kontrol eden sakin
bir dongu (bexi-telegram/hourly_digest.py ile ayni desen).

Kullanim:
  nohup python3 ~/ark-system/agents/security-loop/watch_commits.py \
    > ~/ark-system/agents/security-loop/watch.log 2>&1 &
  disown
"""

import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = Path(__file__).parent / ".last_reviewed_commit"
INTERVAL_SECONDS = 900  # 15 dakikada bir kontrol

REVIEW_TIMEOUT_SECONDS = 1800  # tek commit incelemesi icin ust sinir

# Cevabin PARSE edilebilir olmasi icin Codex'e bu sabit son-satir formatini
# zorunlu tutuyoruz - serbest metin eslestirmesi (ör. "vuln" kelimesi arama)
# guvenilmez olurdu.
REVIEW_PROMPT = (
    "Bu commit'i gercek guvenlik acigi ve gercek bug acisindan incele "
    "(stil/tercih degil, somut ve calistirilabilir sorunlar). Bulgu varsa "
    "kisaca (dosya:satir + ne yanlis + neden onemli) acikla. Cevabinin EN "
    "SONUNDA, baska hicbir sey olmadan, tek satir halinde su ikiden birini "
    "yaz: 'SONUC: TEMIZ' (gercek sorun yoksa) veya 'SONUC: SORUNLU' "
    "(en az bir gercek sorun varsa)."
)

# commit'teki dosya yoluna gore hangi "ajan" etkilendi - Telegram mesajinda
# okunakli olsun diye.
AGENT_PATH_MAP = [
    ("agents/ajan1/", "Ajan 1 (lead scraping/scoring)"),
    ("agents/ajan2/", "Ajan 2 (video prompt)"),
    ("agents/ajan3/", "Ajan 3 (site-assembler)"),
    ("agents/ajan-arge/", "Ajan Ar-Ge (model benchmark)"),
    ("agents/bexi-telegram/", "Bexi Telegram"),
    ("agents/security-loop/", "Guvenlik Ajani (kendisi)"),
    ("voice/", "Sesli Asistan (Bexi)"),
    ("bexi-app/", "Bexi App"),
    ("litellm/", "Model Yonlendirme (litellm)"),
    ("supabase/", "Veritabani semasi"),
    ("template/", "Site sablonu"),
    ("showcases/", "Vitrin siteler"),
]


def _read_env(key: str) -> str:
    env_path = ROOT / "litellm" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


BOT_TOKEN = _read_env("TELEGRAM_BOT_TOKEN")
CHAT_ID = _read_env("TELEGRAM_CHAT_ID")


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    urllib.request.urlopen(url, data=payload, timeout=30)


def get_last_reviewed() -> str:
    if STATE_FILE.exists():
        saved = STATE_FILE.read_text().strip()
        if saved:
            return saved
    # Ilk calistirmada mevcut HEAD'i "incelendi" say - gecmisi topluca
    # taramaz, sadece BUNDAN SONRAKI commit'leri izler.
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    STATE_FILE.write_text(head)
    return head


def set_last_reviewed(sha: str) -> None:
    STATE_FILE.write_text(sha)


def sync_and_list_new_commits(last_sha: str) -> list[str]:
    subprocess.run(
        ["git", "fetch", "origin"], cwd=ROOT, capture_output=True, text=True, timeout=60
    )
    subprocess.run(
        ["git", "merge", "--ff-only", "origin/main"],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    result = subprocess.run(
        ["git", "log", "--reverse", "--format=%H", f"{last_sha}..HEAD"],
        cwd=ROOT, capture_output=True, text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def touched_agents(sha: str) -> str:
    result = subprocess.run(
        ["git", "show", "--name-only", "--format=", sha],
        cwd=ROOT, capture_output=True, text=True,
    )
    files = [f for f in result.stdout.splitlines() if f.strip()]
    agents: list[str] = []
    for f in files:
        for prefix, name in AGENT_PATH_MAP:
            if f.startswith(prefix) and name not in agents:
                agents.append(name)
    return ", ".join(agents) if agents else "Genel (eslesmeyen dosyalar)"


def review_commit(sha: str) -> str:
    return _run_codex_review(["--commit", sha], tag=sha)


def review_uncommitted() -> str:
    return _run_codex_review(["--uncommitted"], tag="uncommitted")


def _run_codex_review(extra_args: list[str], tag: str) -> str:
    out_file = Path(f"/tmp/security_loop_review_{tag}.txt")
    out_file.unlink(missing_ok=True)
    try:
        subprocess.run(
            [
                "codex", "exec", "review",
                *extra_args,
                "--output-last-message", str(out_file),
                REVIEW_PROMPT,
            ],
            cwd=ROOT, capture_output=True, text=True, timeout=REVIEW_TIMEOUT_SECONDS,
        )
        if out_file.exists():
            return out_file.read_text().strip()
    finally:
        out_file.unlink(missing_ok=True)
    return ""


def manual_scan_now() -> str:
    """Kaan Telegram'dan "tara" yazinca cagirilir (2026-07-24, elle tetikleme
    talebi). Commit edilmemis degisiklik varsa onu, yoksa son commit'i tarar."""
    status = subprocess.run(
        ["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()

    if status:
        review = review_uncommitted()
        label = "Commit edilmemiş değişiklikler"
    else:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
        review = review_commit(sha)
        label = f"Son commit ({sha[:7]})"

    verdict = "SORUNLU" if is_problematic(review) else "temiz"
    body = review if review else "(bos cevap - inceleme calismamis olabilir)"
    return f"Güvenlik taraması - {label}\nSonuç: {verdict}\n\n{body[:1200]}"


def is_problematic(review_text: str) -> bool:
    """Codex'in zorunlu son-satir formatina gore karar verir. Beklenen
    formatta bir cevap gelmezse GUVENLI TARAFTA HATA YAP - sessizce
    'temiz' sayma, Telegram'a haber ver ki Kaan farkinda olsun."""
    if not review_text:
        return True
    for line in reversed(review_text.strip().splitlines()):
        line = line.strip().upper()
        if line == "SONUC: TEMIZ":
            return False
        if line == "SONUC: SORUNLU":
            return True
        if line:
            break
    return True  # beklenmeyen format -> temkinli ol


def main() -> None:
    print(f"[guvenlik-dongusu] baslatildi {time.ctime()}", flush=True)
    last_sha = get_last_reviewed()
    while True:
        try:
            commits = sync_and_list_new_commits(last_sha)
        except Exception as exc:
            print(f"[guvenlik-dongusu] git hatasi: {exc}", flush=True)
            time.sleep(INTERVAL_SECONDS)
            continue

        for sha in commits:
            short = sha[:7]
            agent = touched_agents(sha)
            print(f"[guvenlik-dongusu] {short} ({agent}) inceleniyor...", flush=True)
            try:
                review = review_commit(sha)
            except Exception as exc:
                review = f"(inceleme calistirilamadi: {exc})\nSONUC: SORUNLU"

            if is_problematic(review):
                summary = review[:600] if review else "(bos cevap - inceleme calismamis olabilir)"
                try:
                    send_telegram(
                        f"⚠️ Güvenlik taraması - {agent}\n"
                        f"Commit: {short}\n\n{summary}\n\n"
                        f"Düzeltilmeyi bekliyor."
                    )
                    print(f"[guvenlik-dongusu] {short} SORUNLU, Telegram'a bildirildi.", flush=True)
                except Exception as exc:
                    print(f"[guvenlik-dongusu] telegram gonderim hatasi: {exc}", flush=True)
            else:
                print(f"[guvenlik-dongusu] {short} temiz.", flush=True)

            last_sha = sha
            set_last_reviewed(last_sha)

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
