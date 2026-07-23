"""
Ses kaydı (enrollment) — kendi sesini tanıtır.

Birkaç kez konuşursun, ortalama bir "ses parmak izi" çıkarıp kaydeder.
hands_free.py bunu kullanarak sadece SENİN sesine uyanır; başkası
"Bexi uyan" derse yok sayar.

Kullanım:
    python enroll_voice.py

Sonunda benzerlik skorlarını yazdırır — eşiği (SPEAKER_THRESHOLD) buna
bakarak ayarlarsın. Başkasının sesiyle de test etmen önerilir:
    python enroll_voice.py --test
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import webrtcvad

SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)
SILENCE_TIMEOUT_MS = 800
VAD_AGGRESSIVENESS = 2

VOICEPRINT_PATH = Path.home() / ".config" / "bexi" / "voiceprint.npy"
N_SAMPLES = 5
MIN_SECONDS = 1.5

PROMPTS = [
    "Bexi uyan",
    "Bexi uyan, git status çalıştır",
    "Bexi uyan, şu dosyayı oku bakalım",
    "Bexi uyan",
    "Bexi uyan, projeyi derle ve testleri çalıştır",
]


def record_once(vad: webrtcvad.Vad, min_seconds: float = MIN_SECONDS) -> np.ndarray:
    frames: list[np.ndarray] = []
    silence_ms = 0
    started = False
    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=FRAME_SAMPLES
    ) as stream:
        while True:
            block, _ = stream.read(FRAME_SAMPLES)
            block = np.asarray(block).flatten()
            if len(block) != FRAME_SAMPLES:
                continue
            if vad.is_speech(block.tobytes(), SAMPLE_RATE):
                started = True
                silence_ms = 0
                frames.append(block)
            elif started:
                silence_ms += FRAME_MS
                frames.append(block)
                if silence_ms >= SILENCE_TIMEOUT_MS:
                    break
    return np.concatenate(frames) if frames else np.zeros(0, dtype=np.int16)


def to_float(audio: np.ndarray) -> np.ndarray:
    return audio.astype(np.float32) / 32768.0


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--test",
        action="store_true",
        help="Kayıtlı parmak izine karşı tek bir örnek test eder (başkasının sesiyle dene)",
    )
    args = ap.parse_args()

    from resemblyzer import VoiceEncoder

    print("Ses modeli yükleniyor...")
    encoder = VoiceEncoder("cpu")

    # İlk çağrı torch ısınması yüzünden çok yavaş olabilir; şimdi yapalım.
    print("Isıtılıyor...")
    t = time.time()
    encoder.embed_utterance(np.zeros(SAMPLE_RATE * 2, dtype=np.float32) + 1e-4)
    print(f"  ({time.time() - t:.1f}s)")

    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

    # ---------------- TEST MODU ----------------
    if args.test:
        if not VOICEPRINT_PATH.exists():
            sys.exit(f"Parmak izi yok: {VOICEPRINT_PATH}\nÖnce 'python enroll_voice.py' çalıştır.")
        ref = np.load(VOICEPRINT_PATH)
        print("\nKonuş ('Bexi uyan' de). Ctrl+C ile çık.\n")
        try:
            while True:
                audio = record_once(vad)
                dur = len(audio) / SAMPLE_RATE
                if dur < 0.5:
                    continue
                emb = encoder.embed_utterance(to_float(audio))
                score = cosine(emb, ref)
                verdict = "✅ SEN" if score >= 0.75 else "❌ BAŞKASI"
                print(f"  süre={dur:.1f}s  benzerlik={score:.3f}  {verdict}")
        except KeyboardInterrupt:
            print("\nBitti.")
        return

    # ---------------- KAYIT MODU ----------------
    print(f"\n{N_SAMPLES} kez konuşacaksın. Her seferinde normal ses tonunla,")
    print("normal mesafeden konuş. Enter'a bas, konuş, sus.\n")

    embeddings: list[np.ndarray] = []
    for i in range(N_SAMPLES):
        prompt = PROMPTS[i % len(PROMPTS)]
        input(f"[{i+1}/{N_SAMPLES}] Enter'a bas, sonra şunu söyle: \"{prompt}\" ")
        print("  🎤 dinliyorum...")
        audio = record_once(vad)
        dur = len(audio) / SAMPLE_RATE
        if dur < MIN_SECONDS:
            print(f"  ⚠️ çok kısa ({dur:.1f}s), tekrar deneyelim")
            continue
        emb = encoder.embed_utterance(to_float(audio))
        embeddings.append(emb)
        print(f"  ✓ kaydedildi ({dur:.1f}s)")

    if len(embeddings) < 3:
        sys.exit("Yeterli örnek alınamadı. Tekrar dene.")

    # Ortalama parmak izi
    voiceprint = np.mean(embeddings, axis=0)
    voiceprint /= np.linalg.norm(voiceprint)

    VOICEPRINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(VOICEPRINT_PATH, voiceprint)

    # Kendi örneklerinin parmak izine benzerliği -> eşik için alt sınır fikri
    scores = [cosine(e, voiceprint) for e in embeddings]
    print(f"\n✅ Kaydedildi: {VOICEPRINT_PATH}")
    print(f"\nKendi örneklerinin benzerliği:")
    print(f"  en düşük : {min(scores):.3f}")
    print(f"  ortalama : {np.mean(scores):.3f}")
    print(f"  en yüksek: {max(scores):.3f}")
    suggested = max(0.6, min(scores) - 0.05)
    print(f"\nÖnerilen SPEAKER_THRESHOLD: {suggested:.2f}")
    print("  (hands_free.py içinde ayarla)")
    print("\nMutlaka başkasının sesiyle de test et:")
    print("  python enroll_voice.py --test")
    print("  Onun skoru eşiğin ALTINDA kalmalı. Kalmıyorsa eşiği yükselt.")


if __name__ == "__main__":
    main()
