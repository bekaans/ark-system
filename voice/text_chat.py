#!/usr/bin/env python3
"""ARK - Bexi'nin yazili (sesli olmayan) sohbet arayuzu (2026-07-24, Kaan'in
talebi): hands_free.py'nin Claude<->DeepSeek gecis mantigini, ses olmadan,
duz terminal sohbeti olarak sunar.

- Kota dolmaya baslayinca (Claude Code'un kendi rate_limit_event'i "allowed"
  disina cikinca) otomatik olarak DeepSeek'e gecer.
- "deepseek'e gec" / "claude'a don" yazarak elle de gecebilirsin.
- Ayni mantik: CLAUDE_CONFIG_DIR degismez, "-c" ile konusma kesintisiz devam
  eder - hicbir disaridan arac (claudex/CCR) gerekmez.

ONEMLI FARK: bu, Claude Code'un kendi interaktif REPL'i (`/model`, slash
komutlari, canli arac-onay diyaloglari) DEGIL - basit, ust uste soru-cevap
icin. Gercek kodlama oturumlarinda (bu konusma gibi) hala normal `claude`
kullan; bu script sadece hizli/yazili sohbet + otomatik kota gecisi icin.

Kullanim:
  python3 voice/text_chat.py
  (Ctrl+D veya "cikis" ile biter)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEEPSEEK_BASE_URL = "https://openrouter.ai/api"
DEEPSEEK_MODEL = "deepseek/deepseek-v4-pro"
DEEPSEEK_SMALL_MODEL = "nvidia/nemotron-nano-9b-v2:free"

SWITCH_TO_DEEPSEEK_PHRASES = [
    "deepseek'e geç", "deepseeke geç", "deepseek'e gec", "deepseeke gec",
    "deepseek", "deepseek moduna geç", "deepseek moduna gec",
]
SWITCH_TO_CLAUDE_PHRASES = [
    "claude'a dön", "claudeye dön", "claude'a don", "claudeye don", "claude",
]


def _read_openrouter_key() -> str:
    env_path = ROOT / "litellm" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


def ask(prompt: str, is_first_turn: bool, provider: str) -> tuple[str, bool]:
    """hands_free.py'deki ask_claude_code_streaming ile ayni mantik, sesli
    kismi olmadan - metni akarken direkt terminale basar."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if not is_first_turn:
        cmd.append("-c")

    env = None
    if provider == "deepseek":
        env = os.environ.copy()
        env["ANTHROPIC_BASE_URL"] = DEEPSEEK_BASE_URL
        env["ANTHROPIC_MODEL"] = DEEPSEEK_MODEL
        env["ANTHROPIC_SMALL_FAST_MODEL"] = DEEPSEEK_SMALL_MODEL
        env["ANTHROPIC_AUTH_TOKEN"] = _read_openrouter_key()
        env["ANTHROPIC_API_KEY"] = ""

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=env
    )

    full_text: list[str] = []
    rate_limit_hit = False
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "rate_limit_event":
            info = event.get("rate_limit_info", {})
            if info.get("status") not in (None, "allowed"):
                rate_limit_hit = True
            continue

        if event.get("type") != "stream_event":
            continue
        inner = event.get("event", {})
        delta = inner.get("delta", {})
        if delta.get("type") != "text_delta":
            continue
        text = delta.get("text", "")
        if text:
            print(text, end="", flush=True)
            full_text.append(text)

    proc.wait()
    print()

    if proc.returncode != 0:
        err = (proc.stderr.read() if proc.stderr else "").strip()
        print(f"[hata] claude CLI ({provider}, kod {proc.returncode}): {err}", file=sys.stderr)

    return "".join(full_text), rate_limit_hit


def main() -> None:
    provider = "claude"
    is_first_turn = True
    print(f"[bexi-text] hazır (mod: {provider}). Çıkmak için Ctrl+D veya 'çıkış'.")
    while True:
        try:
            text = input("\nSen: ").strip()
        except EOFError:
            print()
            break
        if not text:
            continue
        if text.lower() in ("çıkış", "cikis", "exit", "quit"):
            break

        low = text.strip().lower()
        if low in SWITCH_TO_DEEPSEEK_PHRASES or any(p in low for p in SWITCH_TO_DEEPSEEK_PHRASES if len(p) > 8):
            provider = "deepseek"
            print("[bexi-text] DeepSeek moduna geçildi.")
            continue
        if low in SWITCH_TO_CLAUDE_PHRASES or any(p in low for p in SWITCH_TO_CLAUDE_PHRASES if len(p) > 8):
            provider = "claude"
            print("[bexi-text] Claude moduna geçildi.")
            continue

        print(f"Bexi ({provider}): ", end="", flush=True)
        _, rate_limit_hit = ask(text, is_first_turn, provider)
        is_first_turn = False
        if rate_limit_hit and provider == "claude":
            provider = "deepseek"
            print("[bexi-text] Claude kotası doluyor - DeepSeek'e geçiliyor (otomatik).")


if __name__ == "__main__":
    main()
