"""
Tam otomatik, düşük gecikmeli sesli Claude Code döngüsü.

Gecikmeyi gizlemek için üç teknik:

  1) Sıra Claude'a geçer geçmez, önceden sentezlenmiş bir dolgu cümlesi
     anında çalınır ("bir saniye düşüneyim" gibi). İlk gerçek token gelince
     kesilir.
  2) 7 saniyeyi geçen turlarda watchdog devreye girer ve Claude'un o an
     hangi aracı kullandığını sesli anlatır ("bir dosya okuyorum" vb.).
  3) Cevabın tamamı beklenmez — `--include-partial-messages` ile token token
     akan çıktıda her cümle tamamlandığı anda okunur.

Akış:
  Konuş -> VAD -> Whisper (lokal STT) -> otomatik gönder -> [dolgu sesi]
        -> claude CLI (stream-json) -> [7sn+ ise aktivite anlatımı]
        -> ilk token gelince dolgu kesilir -> cümle cümle TTS

Gereksinim: `claude` CLI kurulu ve login olmalı. Çıkmak için Ctrl+C.
"""

from __future__ import annotations

import difflib
import json
import queue
import random
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel

# --- Ses / kayıt ayarları ---
SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)
# Bu kadar sessizlikten sonra konuşmanın bittiğini varsayar.
# 1000ms (1 sn) rahat bir değer: cümle ortasında duraksasan bile seni
# kesmez. Karşılığında her turda 1 saniye bekleme var. Daha hızlı tepki
# istersen 400-500'e çekebilirsin.
SILENCE_TIMEOUT_MS = 1000
VAD_AGGRESSIVENESS = 2
WHISPER_MODEL_SIZE = "base"

# --- TTS motoru ---
# "piper"      : LOKAL, Türkçe var, ağ gecikmesi sıfır. Düşük gecikme için
#                en iyisi. Kurulum:
#                   pip install piper-tts
#                   python -m piper.download_voices tr_TR-fettah-medium
# "elevenlabs" : En doğal ses. flash modeli düşük gecikmeli ama ÜCRETLİ ve
#                ağ gerektirir. ELEVENLABS_API_KEY ortam değişkeni lazım.
# "edge"       : Ücretsiz, Türkçe var, ama ağ gerektirir (yavaş olabilir).
# "kokoro"     : Lokal ve hızlı ama TÜRKÇE YOK — sadece İngilizce.
TTS_ENGINE = "piper"

PIPER_VOICE = "tr_TR-dfki-medium"  # fettah katalogdan kalkti (2026-07-23), tek Turkce ses bu
PIPER_MODEL_PATH = f"~/.local/share/piper/{PIPER_VOICE}.onnx"

ELEVEN_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # kendi voice id'ini koy
ELEVEN_MODEL = "eleven_flash_v2_5"  # en düşük gecikmeli çok dilli model

EDGE_VOICE = "tr-TR-AhmetNeural"  # alternatif: tr-TR-EmelNeural

KOKORO_VOICE = "af_heart"
KOKORO_LANG = "en-us"

# İlk cümleyi daha çabuk duymak için: ilk parça virgülde de bölünebilir.
# Kısa metin = hızlı sentez = ilk ses daha erken. Sonraki cümleler zaten
# arka planda sentezlendiği için onlarda gerek yok.
FIRST_CHUNK_SPLIT_ON_COMMA = True

# --- Uyandırma (wake word) ---
# Uyku modunda her duyduğu Claude'a GİTMEZ; sadece bu kelimelerden biri
# geçerse uyanır. Whisper özel isimleri bozabildiği için ("Bexi" -> "beksi",
# "peksi"...) bulanık eşleştirme yapıyoruz, varyantları da listeledim.
WAKE_WORDS = ["bexi", "beksi", "peksi", "bexy", "bekси", "becksi", "beksy"]
# Uyandırma fiili. True ise sadece "Bexi uyan" uyandırır, tek başına "Bexi"
# uyandırmaz — yanlış tetiği ciddi biçimde azaltır.
REQUIRE_WAKE_VERB = True
WAKE_VERBS = ["uyan", "uyansana", "uyanır"]
# 0.92: "beksir/beksin" gibi yakın kelimeleri eler (0.909), gerçek varyantları
# geçirir (1.0). Düşürürsen daha kolay uyanır ama yanlış tetik artar.
WAKE_FUZZY_THRESHOLD = 0.92
# Uyandırma kelimesi cümlenin ilk bu kadar kelimesi içinde olmalı. Doğal
# kullanım "Bexi, şunu yap" şeklinde; bu kısıt yanlış tetiği çok azaltıyor.
WAKE_MAX_TOKEN_INDEX = 2

# Uykuya geçme fiili. Uyku emri SADECE uyandırma kelimesiyle birlikte
# geçerli: "Bexi uyu" / "Bexi kapan". Böylece "şu dosyayı kapat" gibi
# gerçek komutlar yanlışlıkla uyku emri sanılamaz (Kaan: "bexi uyu, kapan").
# Not: "kapat" bilerek EKLENMEDI - "Bexi kapat şunu" gibi gerçek bir komutla
# çakışırdı. "kapan" ise komut başında nadir, güvenli.
SLEEP_VERBS = ["uyu", "uyusana", "kapan"]

# Uyandıktan sonra bu kadar süre HİÇ konuşmazsan kendi uykuya döner.
# Her konuşmanda sayaç sıfırlanır, yani sürekli sohbet ederken hiç kapanmaz.
ACTIVE_WINDOW_SECONDS = 600.0  # 10 dakika

# Uyanınca / uyurken ne desin (kısa tutuyoruz, gecikme hissi olmasın)
WAKE_ACK = "Efendim?"

# --- Unutma komutu ---
# "unut gitsin" dersin, sana son konuştuğunuz konuyu sorar, onaylarsan
# Claude'a o konuyu görmezden gelmesi talimatını gönderir.
# NOT: bu davranışsal unutma. Claude Code oturumdan bir parçayı cerrahi
# olarak silmeye izin vermiyor; token'lar context'te kalır ama Claude o
# konuyu bir daha kullanmaz ve hafıza notlarından silmesi istenir.
FORGET_PHRASES = [
    "unut gitsin", "unut bunu", "bunu unut", "sil gitsin",
    "boş ver gitsin", "bos ver gitsin", "unut",
]
FORGET_FUZZY_THRESHOLD = 0.85
YES_WORDS = ["evet", "tamam", "olur", "aynen", "he", "hı hı", "doğru", "dogru"]
NO_WORDS = ["hayır", "hayir", "yok", "iptal", "vazgeçtim", "vazgectim", "boşver", "bosver"]
# Onay sorusuna cevap için ne kadar beklesin
CONFIRM_TIMEOUT_SECONDS = 12.0
SLEEP_ACK = "Tamam, uyuyorum."

# --- Misafir ses protokolu (2026-07-24, Kaan'in tanimi) ---
# Kaan'in sesinden FARKLI bir ses Bexi'ye seslendiginde (ismini soyleyip
# soru sordugunda): her yeni ses icin BIR kez asagidaki karsilama soylenir.
# Kaan "sorun yok, konusabilirsin/tanisabilirsin" derse o misafirin sesi o
# konusma icin 2. ses olarak kaydedilir (SADECE RAM - diske asla yazilmaz).
# Konusma bitince (uyku) misafir sesleri silinir. Ayni durum tekrar
# ederse Bexi sebebini aciklar (guvenlik + kendi sunucuya tasininca rahat
# konusma sozu).
GUEST_PROTOCOL = True
# Ayni misafiri (bu konusma icinde) tekrar tanimak icin benzerlik esigi.
GUEST_MATCH_THRESHOLD = 0.70
GUEST_GREETING = (
    "Seni tanımıyorum. Şu an gelişim aşamasında olduğum için seninle "
    "konuşmak istenmeyen sonuçlara yol açabilir. Kaan, evet konuşabilirsin "
    "diyecek kadar sana güveniyorsa, önce tanışır sonra konuşabiliriz."
)
GUEST_DELETED_EXPLANATION = (
    "Herhangi bir güvenlik açığı olmasın diye misafir seslerini her "
    "konuşma bitince siliyorum. Kendi veri sunucumuza geçtiğimizde daha "
    "rahat konuşabileceğiz. Kaan yine onay verirse şimdi de tanışabiliriz."
)
GUEST_APPROVED_ACK = "Tamam, tanıştık. Artık konuşabilirsin."
# Kaan'in onay kaliplari (kucuk harf, noktalamasiz metinde aranir)
GUEST_APPROVE_PHRASES = [
    "tanışabilirsin", "tanisabilirsin",
    "konuşabilirsin", "konusabilirsin",
    "sorun yok konuş", "sorun yok konus",
    "konuşabilirsiniz", "konusabilirsiniz",
]
# Misafir ISIMLERI hatirlanir (SADECE isim - konusma icerigi/ses vektoru
# DEGIL). Kaan'in kurali: "sadece isimlerini hatirla naber vb de ama
# simdiden soyle ne konustugumuzu hatirlamiyorum, sebebi guvenlik."
GUEST_NAMES_PATH = Path.home() / ".config" / "bexi" / "guest_names.json"
GUEST_MEMORY_DISCLOSURE = (
    "Bu arada şunu baştan söyleyeyim, ismini hatırlarım ama ne "
    "konuştuğumuzu hatırlamam. Güvenlik gereği misafirlerle geçici "
    "konuşuyorum, kendi veri sunucumuza geçince bu değişecek."
)


def load_guest_names() -> set[str]:
    try:
        return set(json.loads(GUEST_NAMES_PATH.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def save_guest_names(names: set[str]) -> None:
    try:
        GUEST_NAMES_PATH.parent.mkdir(parents=True, exist_ok=True)
        GUEST_NAMES_PATH.write_text(
            json.dumps(sorted(names), ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass


_NAME_RE = re.compile(
    r"\b(?:benim\s+)?(?:ad[iı]m|ismim)\s+([a-zçğıöşü]{2,20})\b",
    re.IGNORECASE,
)
_NAME_STOPWORDS = {"ne", "yok", "var", "bir", "sen", "ben", "bu", "su", "şu"}


def extract_guest_name(text: str) -> str | None:
    """Misafirin kendini tanittigi ismi cikarir - SADECE net kaliplardan
    ('adim X' / 'ismim X' / 'benim adim X'). 'ben X' gibi belirsiz kalip
    KASITLI olarak desteklenmez (yanlis isim yakalamamak icin)."""
    m = _NAME_RE.search(text)
    if not m:
        return None
    name = m.group(1).strip().lower()
    if name in _NAME_STOPWORDS:
        return None
    return name.capitalize()

# --- Parmak şıklatma ile uyandırma ---
# KAPALI ve KAPALI KALACAK (Kaan'ın kararı, 2026-07-24: "parmak şıklatma ile
# uyanma falan yok, sadece 'Bexi uyan'"). Kod duruyor ama ENABLE_SNAP=False
# olduğu sürece hiçbir şıklatma kod yolu çalışmaz. AÇMA.
ENABLE_SNAP = False
SNAP_PEAK_THRESHOLD = 0.35   # 0-1, tam ölçeğe göre tepe genlik
SNAP_QUIET_BEFORE = 0.06     # şıklatmadan önceki sessizlik eşiği (RMS)
SNAP_DECAY_RATIO = 0.35      # şıklatma hızlı sönmeli (kısa transient)
SNAP_QUIET_FRAMES = 8        # öncesinde bu kadar frame sessiz olmalı

# --- Konuşmacı tanıma (sadece senin sesine uyansın) ---
# Açmadan önce: python enroll_voice.py
# Kapalıysa herkesin sesi "Bexi uyan" diyerek uyandırabilir.
SPEAKER_VERIFY = True
SPEAKER_THRESHOLD = 0.75  # enroll_voice.py sana uygun değeri önerir
VOICEPRINT_PATH = Path.home() / ".config" / "bexi" / "voiceprint.npy"
# True: uyanıkken gelen HER cümleyi de doğrular (yanındaki biri konuşursa
#       Claude'a gitmez). False: sadece uyandırma anında doğrular.
VERIFY_EVERY_UTTERANCE = True
# Konuşmacı doğrulaması için gereken en az ses süresi. Bunun altındaki
# kayıtlarda gömme vektörü güvenilmez oluyor.
SPEAKER_MIN_SECONDS = 0.6
# Çok kısa kayıtlarda ne yapılsın?
#   True  : geçir (senin "evet", "dur" gibi kısa komutların engellenmez,
#           ama başkasının kısa sözü de geçebilir)
#   False : reddet (daha güvenli, ama kısa komutlarını da eler)
ALLOW_SHORT_UNVERIFIED = True

# Whisper'a dil sabitle. None = otomatik algıla (kısa cümlelerde yanlış dil
# algılayıp saçma transkripsiyon üretebiliyor). Türkçe için "tr".
STT_LANGUAGE = "tr"

# Sıra Claude'a geçtiğinde çalınacak dolgular. Claude'a hiç gitmez, tamamen
# lokal — token maliyeti sıfır.
FILLER_PHRASES = [
    "Hmm, bir saniye düşüneyim.",
    "Bakıyorum şimdi.",
    "Bir saniye.",
    "Tamam, bakalım.",
]

# Bu süreyi geçen turlarda Claude'un ne yaptığı sesli anlatılmaya başlar.
LONG_WAIT_THRESHOLD_SECONDS = 7.0

# --- Bexi UI (Mac/iPhone uygulaması) ---
# True ise ui_bridge.py'nin SSE sunucusu başlar; Mac/iOS Bexi uygulamaları
# oradan canlı durum/konuşma akışı alır. False ise emit() no-op, motor
# davranışı bit düzeyinde aynı kalır.
UI_ENABLED = True

try:
    from ui_bridge import bridge as _ui_bridge
except ImportError:
    _ui_bridge = None


def ui_emit(type_: str, **fields) -> None:
    if UI_ENABLED and _ui_bridge is not None:
        _ui_bridge.emit(type_, **fields)

# Belli bir tur sayısından sonra Claude Code oturumunu sıfırlar.
# 0 = hiç sıfırlama (VARSAYILAN).
#
# Kapalı, çünkü Claude Code zaten context'i kendi yönetiyor (otomatik
# compaction) ve kalıcı hafıza skill'i önemli notları diske yazıp geri
# okuyor. Zorla sıfırlama bu mekanizmaların üstüne biner, iş ortasında
# gereksiz bağlam kaybına yol açar.
#
# Yine de bir tavan istersen sayı ver (ör. 40).
MAX_TURNS_PER_SESSION = 0

CACHE_DIR = Path.home() / ".cache" / "pipecat" / "kokoro-onnx"
KOKORO_MODEL_PATH = CACHE_DIR / "kokoro-v1.0.onnx"
KOKORO_VOICES_PATH = CACHE_DIR / "voices-v1.0.bin"

SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")
FIRST_CHUNK_RE = re.compile(r"(?<=[.!?,:;])\s+")

TOOL_NARRATIONS = {
    "Bash": "bir komut çalıştırıyorum",
    "Read": "bir dosya okuyorum",
    "Write": "bir dosya yazıyorum",
    "Edit": "dosyayı düzenliyorum",
    "MultiEdit": "dosyalarda değişiklik yapıyorum",
    "Grep": "kodda arama yapıyorum",
    "Glob": "dosyaları tarıyorum",
    "WebSearch": "web'de araştırıyorum",
    "WebFetch": "bir sayfayı inceliyorum",
    "Task": "bir alt görev başlatıyorum",
    "TodoWrite": "yapılacaklar listesini güncelliyorum",
    "NotebookEdit": "notebook'u düzenliyorum",
}


def describe_tool(name: str) -> str:
    return TOOL_NARRATIONS.get(name, f"{name} kullanıyorum")


# ---------------------------------------------------------------- TTS backend


class TTSBackend:
    """Metni (samples: float32 mono, samplerate) çiftine çevirir."""

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        raise NotImplementedError


class PiperBackend(TTSBackend):
    """Piper — tamamen lokal, CPU'da gerçek zamandan hızlı, Türkçe sesi var.
    Ağ gecikmesi sıfır. Düşük gecikme için en iyi seçenek.

    Ses modelini ilk çalıştırmada indirir:
        python -m piper.download_voices tr_TR-fettah-medium
    """

    def __init__(self):
        from piper import PiperVoice

        model = Path(PIPER_MODEL_PATH).expanduser()
        if not model.exists():
            raise FileNotFoundError(
                f"Piper ses modeli bulunamadı: {model}\n"
                f"İndirmek için: python -m piper.download_voices {PIPER_VOICE}"
            )
        self.voice = PiperVoice.load(str(model))

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        chunks = []
        sr = 22050
        for chunk in self.voice.synthesize(text):
            sr = chunk.sample_rate
            arr = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            chunks.append(arr)
        if not chunks:
            return np.zeros(0, dtype=np.float32), sr
        audio = np.concatenate(chunks).astype(np.float32) / 32768.0
        return audio, sr


class EdgeBackend(TTSBackend):
    """Microsoft Edge TTS — Türkçe doğal ses, ücretsiz, ama ağ gerektirir.

    Not: önceki sürüm her cümlede asyncio.run() çağırıyordu; bu her seferinde
    yeni bir event loop kurulması demekti. Artık kalıcı bir loop arka planda
    dönüyor.
    """

    def __init__(self):
        import asyncio
        import io

        import edge_tts
        import soundfile as sf

        self._asyncio = asyncio
        self._edge_tts = edge_tts
        self._sf = sf
        self._io = io

        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

    async def _collect(self, text: str) -> bytes:
        comm = self._edge_tts.Communicate(text, EDGE_VOICE)
        buf = bytearray()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                buf += chunk["data"]
        return bytes(buf)

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        fut = self._asyncio.run_coroutine_threadsafe(self._collect(text), self._loop)
        mp3 = fut.result()
        data, sr = self._sf.read(self._io.BytesIO(mp3), dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)
        return data, sr


class ElevenLabsBackend(TTSBackend):
    """ElevenLabs — en doğal ses. flash modeli çok düşük gecikmeli ama
    ücretli ve ağ gerektirir. ELEVENLABS_API_KEY ortam değişkeni gerekir."""

    def __init__(self):
        import io
        import os

        import soundfile as sf
        from elevenlabs.client import ElevenLabs

        key = os.getenv("ELEVENLABS_API_KEY")
        if not key:
            raise RuntimeError("ELEVENLABS_API_KEY tanımlı değil.")
        self.client = ElevenLabs(api_key=key)
        self._sf = sf
        self._io = io

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        stream = self.client.text_to_speech.convert(
            voice_id=ELEVEN_VOICE_ID,
            model_id=ELEVEN_MODEL,
            text=text,
            output_format="mp3_22050_32",
        )
        buf = bytearray()
        for chunk in stream:
            if chunk:
                buf += chunk
        data, sr = self._sf.read(self._io.BytesIO(bytes(buf)), dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)
        return data, sr


class KokoroBackend(TTSBackend):
    """Lokal ve hızlı ama TÜRKÇE DESTEKLEMİYOR. Sadece İngilizce için."""

    def __init__(self):
        from kokoro_onnx import Kokoro

        ensure_kokoro_files()
        self.kokoro = Kokoro(str(KOKORO_MODEL_PATH), str(KOKORO_VOICES_PATH))

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        return self.kokoro.create(text, voice=KOKORO_VOICE, lang=KOKORO_LANG)


_BACKENDS = {
    "piper": PiperBackend,
    "edge": EdgeBackend,
    "elevenlabs": ElevenLabsBackend,
    "kokoro": KokoroBackend,
}


def make_tts_backend() -> TTSBackend:
    try:
        return _BACKENDS[TTS_ENGINE]()
    except KeyError:
        raise ValueError(
            f"Bilinmeyen TTS_ENGINE: {TTS_ENGINE}. "
            f"Seçenekler: {', '.join(_BACKENDS)}"
        ) from None


def ensure_kokoro_files() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    urls = {
        KOKORO_MODEL_PATH: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
        KOKORO_VOICES_PATH: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
    }
    import requests

    for path, url in urls.items():
        if not path.exists():
            print(f"[kurulum] {path.name} indiriliyor...")
            resp = requests.get(url, stream=True, timeout=300)
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)


# ------------------------------------------------------------ metin temizleme

CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`([^`]*)`")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
MD_MARKS_RE = re.compile(r"[*_#>|]+")
PATH_RE = re.compile(r"(?:/[\w.\-]+){2,}")


def clean_for_speech(text: str) -> str:
    """Markdown/kod/dosya yollarını sesli okumaya uygun hale getirir.
    Bunlar olmadan TTS 'yıldız yıldız backtick def main parantez' diye
    okuyup kulak tırmalıyor."""
    text = CODE_BLOCK_RE.sub(" kod bloğu ", text)
    text = INLINE_CODE_RE.sub(r"\1", text)
    text = MD_LINK_RE.sub(r"\1", text)
    text = PATH_RE.sub(" dosya yolu ", text)
    text = MD_MARKS_RE.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -------------------------------------------------------------------- kayıt


def _fuzzy_hit(word: str, candidates: list[str], threshold: float) -> bool:
    word = word.strip(".,!?;:").lower()
    if not word:
        return False
    for cand in candidates:
        if difflib.SequenceMatcher(None, word, cand).ratio() >= threshold:
            return True
    return False


def match_wake_word(text: str) -> tuple[bool, str]:
    """Metinde uyandırma kelimesi var mı? Varsa (True, kalan komut) döner.

    'Bexi uyan, şu dosyayı oku' -> (True, 'şu dosyayı oku')
    'Bexi'                      -> (True, '')
    'hava nasıl'                -> (False, '')
    """
    tokens = text.split()
    for i, tok in enumerate(tokens):
        if i > WAKE_MAX_TOKEN_INDEX:
            break
        if _fuzzy_hit(tok, WAKE_WORDS, WAKE_FUZZY_THRESHOLD):
            rest = tokens[i + 1:]
            # "Bexi uyan" gibi fiil şartı varsa, hemen ardından gelmeli
            if REQUIRE_WAKE_VERB:
                if not rest or not _fuzzy_hit(rest[0], WAKE_VERBS, 0.8):
                    return False, ""
                rest = rest[1:]
            else:
                while rest and _fuzzy_hit(rest[0], WAKE_VERBS, 0.8):
                    rest = rest[1:]
            return True, " ".join(rest).strip(" ,.")
    return False, ""


def is_sleep_command(text: str) -> bool:
    """Sadece "Bexi uyu" kalıbı uykuya geçirir.

    Uyandırma kelimesi şart olduğu için "şu dosyayı kapat" gibi gerçek
    komutlar asla uyku emri sanılamaz.
    """
    tokens = [t.strip(".,!?;:").lower() for t in text.split()]
    tokens = [t for t in tokens if t]

    for i, tok in enumerate(tokens):
        if i > WAKE_MAX_TOKEN_INDEX:
            break
        if _fuzzy_hit(tok, WAKE_WORDS, WAKE_FUZZY_THRESHOLD):
            rest = tokens[i + 1:]
            return bool(rest) and _fuzzy_hit(rest[0], SLEEP_VERBS, 0.85)
    return False


def _looks_like_snap(frames: list[np.ndarray], idx: int) -> bool:
    """Kısa, yüksek genlikli, hızlı sönen ve öncesinde sessizlik olan bir
    transient mi? Parmak şıklatması buna benziyor."""
    if idx < SNAP_QUIET_FRAMES or idx + 2 >= len(frames):
        return False

    peak = np.abs(frames[idx]).max() / 32768.0
    if peak < SNAP_PEAK_THRESHOLD:
        return False

    before = frames[idx - SNAP_QUIET_FRAMES:idx]
    bg = max(float(np.sqrt(np.mean(f.astype(np.float64) ** 2))) for f in before) / 32768.0
    if bg > SNAP_QUIET_BEFORE:
        return False  # öncesi sessiz değil -> muhtemelen konuşma

    after_peak = max(np.abs(frames[idx + 1]).max(), np.abs(frames[idx + 2]).max()) / 32768.0
    return after_peak < peak * SNAP_DECAY_RATIO


def listen_for_trigger(vad: webrtcvad.Vad) -> tuple[str, np.ndarray | None]:
    """Uyku modunda dinler. Döndürür:
        ("snap", None)      -> parmak şıklatması algılandı
        ("speech", audio)   -> konuşma algılandı (wake word kontrolü çağırana ait)
    """
    hint = "'Bexi uyan' de" if REQUIRE_WAKE_VERB else "'Bexi' de"
    print("\n😴 Uykuda — " + hint + (" ya da parmak şıklat" if ENABLE_SNAP else "") + "...")
    recent: list[np.ndarray] = []
    speech_frames: list[np.ndarray] = []
    silence_ms = 0
    speech_started = False

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=FRAME_SAMPLES
    ) as stream:
        while True:
            block, _ = stream.read(FRAME_SAMPLES)
            block = np.asarray(block).flatten()
            if len(block) != FRAME_SAMPLES:
                continue

            recent.append(block)
            if len(recent) > SNAP_QUIET_FRAMES + 4:
                recent.pop(0)

            if ENABLE_SNAP and not speech_started:
                # tamponun sonundan 3 frame geriye bak (sönüm için 2 frame lazım)
                probe = len(recent) - 3
                if probe > 0 and _looks_like_snap(recent, probe):
                    return "snap", None

            is_speech = vad.is_speech(block.tobytes(), SAMPLE_RATE)
            if is_speech:
                speech_started = True
                silence_ms = 0
                speech_frames.append(block)
            elif speech_started:
                silence_ms += FRAME_MS
                speech_frames.append(block)
                if silence_ms >= SILENCE_TIMEOUT_MS:
                    return "speech", np.concatenate(speech_frames)


def transcribe_and_verify(
    audio: np.ndarray,
    whisper: WhisperModel,
    verifier: "SpeakerVerifier | None",
) -> tuple[str, bool, float | None]:
    """Transkripsiyon ve konuşmacı doğrulamasını PARALEL çalıştırır.

    İkisi de aynı sesi kullanıyor ama birbirinden bağımsız. Seri
    çalıştırılırsa doğrulama (~50ms) doğrudan kritik yola eklenir ve dolgu
    sesinin başlamasını da geciktirir. Paralel çalıştırınca Whisper'ın
    arkasına gizleniyor, net maliyet ~0 oluyor.
    """
    if verifier is None:
        return transcribe(audio, whisper), True, None

    result: dict = {}

    def _verify():
        try:
            result["owner"], result["score"] = verifier.is_owner(audio)
        except Exception as exc:  # noqa: BLE001
            print(f"[uyarı] ses doğrulama hatası: {exc}", file=sys.stderr)
            result["owner"], result["score"] = True, None

    t = threading.Thread(target=_verify, daemon=True)
    t.start()
    text = transcribe(audio, whisper)
    t.join()
    return text, result.get("owner", True), result.get("score")


def fmt_score(score: float | None) -> str:
    return "çok kısa, doğrulanamadı" if score is None else f"benzerlik {score:.3f}"


class SpeakerVerifier:
    """Sesin kayıtlı parmak izine ait olup olmadığını kontrol eder.

    Not: modelin İLK çağrısı torch ısınması yüzünden çok yavaş olabiliyor
    (ölçümde ~30sn). Bu yüzden başlangıçta ısıtıyoruz — yoksa ilk
    "Bexi uyan" komutu dakikalarca bekletirdi.
    """

    def __init__(self):
        from resemblyzer import VoiceEncoder

        if not VOICEPRINT_PATH.exists():
            raise FileNotFoundError(
                f"Ses parmak izi bulunamadı: {VOICEPRINT_PATH}\n"
                f"Önce şunu çalıştır: python enroll_voice.py\n"
                f"(ya da hands_free.py içinde SPEAKER_VERIFY = False yap)"
            )
        self.encoder = VoiceEncoder("cpu")
        self.reference = np.load(VOICEPRINT_PATH)
        self.reference = self.reference / np.linalg.norm(self.reference)

        # ısıtma
        self.encoder.embed_utterance(
            np.zeros(SAMPLE_RATE * 2, dtype=np.float32) + 1e-4
        )

    def embedding(self, audio_int16: np.ndarray) -> np.ndarray | None:
        """Normalize edilmis ses vektoru. Ses cok kisaysa None doner.
        Misafir ses protokolu icin de kullanilir - SADECE RAM'de yasar,
        asla diske yazilmaz."""
        if len(audio_int16) < SAMPLE_RATE * SPEAKER_MIN_SECONDS:
            return None
        wav = audio_int16.astype(np.float32) / 32768.0
        emb = self.encoder.embed_utterance(wav)
        return emb / np.linalg.norm(emb)

    def score(self, audio_int16: np.ndarray) -> float | None:
        """Benzerlik skoru (0-1). Ses çok kısaysa None döner."""
        emb = self.embedding(audio_int16)
        if emb is None:
            return None
        return float(np.dot(emb, self.reference))

    def is_owner(self, audio_int16: np.ndarray) -> tuple[bool, float | None]:
        s = self.score(audio_int16)
        if s is None:
            # Çok kısa: güvenilir doğrulama yapılamıyor.
            return ALLOW_SHORT_UNVERIFIED, None
        return s >= SPEAKER_THRESHOLD, s


def _strip_wake(tokens: list[str]) -> list[str]:
    out = []
    skip_next_verb = False
    for i, t in enumerate(tokens):
        if i <= WAKE_MAX_TOKEN_INDEX and _fuzzy_hit(t, WAKE_WORDS, WAKE_FUZZY_THRESHOLD):
            skip_next_verb = True
            continue
        if skip_next_verb and _fuzzy_hit(t, WAKE_VERBS, 0.8):
            skip_next_verb = False
            continue
        skip_next_verb = False
        out.append(t)
    return out


def mentions_bexi(text: str) -> bool:
    """Cumlenin HERHANGI bir yerinde Bexi'nin adi geciyor mu? (Misafir ses
    protokolu icin - uyandirma kurali gibi 'ilk 2 kelime' kisiti YOK,
    'ismini soyleyip soru sordugunda' tanimina uyar.)"""
    return any(
        _fuzzy_hit(t, WAKE_WORDS, WAKE_FUZZY_THRESHOLD) for t in text.split()
    )


def is_guest_approval(text: str) -> bool:
    """Kaan'in 'sorun yok, konusabilirsin / tanisabilirsin' tarzi onayi."""
    low = " ".join(t.strip(".,!?;:").lower() for t in text.split())
    return any(p in low for p in GUEST_APPROVE_PHRASES)


def guest_best_score(emb: np.ndarray, known: list[np.ndarray]) -> float:
    """Bir ses vektorunun bilinen misafir vektorlerine en yuksek benzerligi."""
    if not known:
        return 0.0
    return max(float(np.dot(emb, k)) for k in known)


# "bu konuyu komple unut" gibi TEK ANLAMLI, meta-unutma kaliplari. Bunlar
# cumlenin herhangi yerinde gecerse yeter (uzunluk siniri yok) - cunku
# "komple unut / konuyu unut" bir icerik komutu (orn "şu satırı unut") ile
# karisamaz. Kaan'in ornegi: "Bexi bu konuyu komple unut".
FORGET_STRONG_MARKERS = [
    "komple unut", "konuyu unut", "bu konuyu unut", "bu konuyu komple unut",
    "hepsini unut", "komple sil", "unut gitsin", "sil gitsin",
    "boş ver gitsin", "bos ver gitsin",
]


def is_forget_command(text: str) -> bool:
    """Unutma emri mi? Iki yol:
    1) Guclu, tek anlamli meta-isaret ("komple unut" vb) - cumlenin herhangi
       yerinde gecerse yeter.
    2) Kisa ve cumlenin TAMAMI unutma emri ("unut", "bunu unut") - "şu satırı
       unut" gibi icerik komutlarini yanlis tetiklememek icin <=3 kelime siniri."""
    tokens = [t.strip(".,!?;:").lower() for t in text.split()]
    tokens = [t for t in tokens if t]
    core = " ".join(_strip_wake(tokens))
    if not core:
        return False
    if any(m in core for m in FORGET_STRONG_MARKERS):
        return True
    if len(core.split()) > 3:
        return False
    return any(
        difflib.SequenceMatcher(None, core, ph).ratio() >= FORGET_FUZZY_THRESHOLD
        for ph in FORGET_PHRASES
    )


def classify_yes_no(text: str) -> bool | None:
    """True=evet, False=hayır, None=anlaşılmadı."""
    tokens = [t.strip(".,!?;:").lower() for t in text.split()]
    tokens = _strip_wake([t for t in tokens if t])
    for t in tokens:
        if _fuzzy_hit(t, NO_WORDS, 0.85):
            return False
    for t in tokens:
        if _fuzzy_hit(t, YES_WORDS, 0.85):
            return True
    return None


def summarize_topic(text: str, max_words: int = 8) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


FORGET_INSTRUCTION = (
    "Aşağıdaki konuyu ve onunla ilgili tüm konuşmayı tamamen görmezden gel. "
    "Bundan sonra bu konuya hiç referans verme, hatırlamıyormuş gibi davran. "
    "Eğer kalıcı hafıza/not sistemin varsa bu konuyla ilgili notları da sil. "
    "Sadece 'Tamam, unuttum.' diye kısaca cevap ver, başka bir şey yazma.\\n\\n"
    "Unutulacak konu: {topic}"
)


def record_until_silence(
    vad: webrtcvad.Vad, timeout: float | None = None
) -> np.ndarray | None:
    """Konuşma bekler, sessizlik gelince kaydı döndürür.

    timeout verilirse ve o süre içinde HİÇ konuşma başlamazsa None döner.
    Bu olmadan fonksiyon konuşma gelene kadar sonsuza kadar bloklardı ve
    'X dakika konuşmazsan uykuya dön' mantığı hiç çalışmazdı.
    """
    print("\n🎤 Dinliyorum...")
    frames: list[np.ndarray] = []
    silence_ms = 0
    speech_started = False
    started_at = time.monotonic()

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=FRAME_SAMPLES
    ) as stream:
        while True:
            block, _ = stream.read(FRAME_SAMPLES)
            block = np.asarray(block).flatten()
            if len(block) != FRAME_SAMPLES:
                continue
            is_speech = vad.is_speech(block.tobytes(), SAMPLE_RATE)

            if not speech_started and timeout is not None:
                if time.monotonic() - started_at >= timeout:
                    return None

            if is_speech:
                speech_started = True
                silence_ms = 0
                frames.append(block)
            elif speech_started:
                silence_ms += FRAME_MS
                frames.append(block)
                if silence_ms >= SILENCE_TIMEOUT_MS:
                    break

    if not frames:
        return None
    return np.concatenate(frames)


def transcribe(audio: np.ndarray, whisper: WhisperModel) -> str:
    audio_f32 = audio.astype(np.float32) / 32768.0
    segments, _ = whisper.transcribe(audio_f32, language=STT_LANGUAGE)
    return " ".join(seg.text.strip() for seg in segments).strip()


# ------------------------------------------------------------------ konuşma


@dataclass
class SpeechItem:
    text: str | None  # None = kapanış sinyali
    is_filler: bool = False
    cached: tuple[np.ndarray, int] | None = None


class Speaker:
    """İKİ AŞAMALI ses hattı: sentezleme ve çalma paralel çalışır.

    Önceki sürümde tek thread önce sentezleyip sonra çalıyordu, yani cümle
    N çalarken cümle N+1 sentezlenmiyordu — her cümle tam sentez gecikmesini
    ödüyordu. Artık:

        text_q -> [sentez thread] -> audio_q -> [çalma thread]

    Cümle N çalarken N+1 arka planda sentezleniyor. Böylece sadece İLK cümle
    gecikmeyi hissettiriyor, gerisi kesintisiz akıyor.

    Ses cihazına erişen TEK yer çalma thread'i (sounddevice global tek akış
    kullandığı için birden fazla thread birbirinin sesini keserdi).
    """

    def __init__(self, backend: TTSBackend):
        self.backend = backend
        self.text_q: queue.Queue[SpeechItem] = queue.Queue()
        # maxsize: sentezlemenin çalmanın çok önüne geçip bellek şişirmesini
        # engeller, ama 3 cümlelik tampon gecikmeyi gizlemeye fazlasıyla yeter.
        self.audio_q: queue.Queue = queue.Queue(maxsize=3)
        self._skip_fillers = threading.Event()
        self._pending = 0
        self._cv = threading.Condition()
        self._closed = False

        threading.Thread(target=self._synth_worker, daemon=True).start()
        threading.Thread(target=self._play_worker, daemon=True).start()

    # -- iç sayaç: wait_until_done için --
    def _inc(self) -> None:
        with self._cv:
            self._pending += 1

    def _dec(self) -> None:
        with self._cv:
            self._pending -= 1
            if self._pending <= 0:
                self._cv.notify_all()

    def _synth_worker(self) -> None:
        while True:
            item = self.text_q.get()
            if item.text is None:
                self.audio_q.put(None)  # çalma thread'ine kapanış sinyali
                return
            try:
                if item.is_filler and self._skip_fillers.is_set():
                    self._dec()
                    continue
                if item.cached is not None:
                    samples, sr = item.cached
                else:
                    samples, sr = self.backend.synth(item.text)
                self.audio_q.put((samples, sr, item.is_filler))
            except Exception as exc:  # noqa: BLE001
                print(f"[uyarı] sentez hatası: {exc}", file=sys.stderr)
                self._dec()

    def _play_worker(self) -> None:
        while True:
            got = self.audio_q.get()
            if got is None:
                return
            samples, sr, is_filler = got
            try:
                if is_filler and self._skip_fillers.is_set():
                    continue
                if len(samples) == 0:
                    continue
                sd.play(samples, sr)
                while True:
                    try:
                        stream = sd.get_stream()
                    except RuntimeError:
                        break
                    if stream is None or not stream.active:
                        break
                    if is_filler and self._skip_fillers.is_set():
                        sd.stop()
                        break
                    time.sleep(0.02)
            except Exception as exc:  # noqa: BLE001
                print(f"[uyarı] çalma hatası: {exc}", file=sys.stderr)
            finally:
                self._dec()

    def say(self, text: str, is_filler: bool = False, cached=None) -> None:
        text = (text or "").strip()
        if not text or self._closed:
            return
        if not is_filler:
            ui_emit("bexi", text=text)  # dolgu cumleleri UI'da gosterilmez
        self._inc()
        self.text_q.put(SpeechItem(text=text, is_filler=is_filler, cached=cached))

    def start_turn(self) -> None:
        self._skip_fillers.clear()

    def cancel_fillers(self) -> None:
        self._skip_fillers.set()

    def wait_until_done(self, timeout: float | None = None) -> None:
        with self._cv:
            self._cv.wait_for(lambda: self._pending <= 0, timeout=timeout)

    def shutdown(self) -> None:
        self._closed = True
        self.text_q.put(SpeechItem(text=None))


# ----------------------------------------------------------------- watchdog


class ActivityTracker:
    """Turun süresini ve Claude'un o anki aktivitesini thread-safe tutar."""

    def __init__(self):
        self.lock = threading.Lock()
        self.turn_start = time.monotonic()
        self.current_activity: str | None = None
        self.first_content_received = False
        self.finished = False

    def set_activity(self, description: str) -> None:
        ui_emit("tool", text=description)
        with self.lock:
            self.current_activity = description

    def mark_first_content(self) -> None:
        with self.lock:
            self.first_content_received = True

    def mark_finished(self) -> None:
        with self.lock:
            self.finished = True

    def snapshot(self) -> tuple[bool, bool, float, str | None]:
        with self.lock:
            return (
                self.finished,
                self.first_content_received,
                time.monotonic() - self.turn_start,
                self.current_activity,
            )


def long_wait_watchdog(tracker: ActivityTracker, speaker: Speaker) -> None:
    """7sn'i geçen turlarda o anki aktiviteyi sesli anlatır, cevap gelene
    kadar ~7sn'de bir günceller."""
    next_threshold = LONG_WAIT_THRESHOLD_SECONDS
    last_phrase: str | None = None

    while True:
        time.sleep(0.5)
        finished, first_content, elapsed, activity = tracker.snapshot()
        if finished or first_content:
            return

        if elapsed >= next_threshold:
            speaker.cancel_fillers()  # kısa dolgunun yerini bu alıyor
            base = activity or "çalışıyorum, biraz sürüyor"
            phrase = f"Hâlâ {base}" if base == last_phrase else base
            speaker.say(phrase)
            last_phrase = base  # önek eklenmemiş hali ile karşılaştır
            next_threshold += LONG_WAIT_THRESHOLD_SECONDS


# -------------------------------------------------------------- claude çağrısı


def ask_claude_code_streaming(
    prompt: str, is_first_turn: bool, speaker: Speaker
) -> str:
    """Claude Code'u stream-json modunda çağırır; cümleler tamamlandıkça
    hemen seslendirir. Tam metni döndürür."""
    ui_emit("state", value="thinking")
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if not is_first_turn:
        cmd.append("-c")

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
    )

    # stderr'i ayrı thread'de boşalt. Aksi halde Claude çok stderr yazarsa
    # 64KB'lık boru dolar, claude yazarken bloklanır, biz de stdout'u
    # beklerken bloklanırız -> kalıcı deadlock.
    stderr_chunks: list[str] = []

    def _drain_stderr():
        if proc.stderr is None:
            return
        for line in proc.stderr:
            stderr_chunks.append(line)

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()

    tracker = ActivityTracker()
    watchdog = threading.Thread(
        target=long_wait_watchdog, args=(tracker, speaker), daemon=True
    )
    watchdog.start()

    buffer = ""
    full_text_parts: list[str] = []
    first_token_received = False
    spoke_anything = False

    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") != "stream_event":
                continue
            inner = event.get("event", {})

            # Araç çağrısı başladı -> aktiviteyi güncelle
            if inner.get("type") == "content_block_start":
                block = inner.get("content_block", {})
                if block.get("type") == "tool_use":
                    tracker.set_activity(describe_tool(block.get("name", "araç")))
                continue

            delta = inner.get("delta", {})
            if delta.get("type") != "text_delta":
                continue
            text = delta.get("text", "")
            if not text:
                continue

            if not first_token_received:
                first_token_received = True
                ui_emit("state", value="speaking")
                speaker.cancel_fillers()
                tracker.mark_first_content()

            buffer += text
            full_text_parts.append(text)

            # İlk parçayı virgülde de bölüyoruz: daha kısa metin = daha hızlı
            # sentez = ilk sesi daha erken duyuyorsun. Sonraki cümleler zaten
            # önceki çalarken arka planda sentezlendiği için gerek yok.
            use_comma = FIRST_CHUNK_SPLIT_ON_COMMA and not spoke_anything
            splitter = FIRST_CHUNK_RE if use_comma else SENTENCE_END_RE

            parts = splitter.split(buffer)
            if len(parts) > 1:
                for sentence in parts[:-1]:
                    cleaned = clean_for_speech(sentence)
                    if cleaned:
                        speaker.say(cleaned)
                        spoke_anything = True
                buffer = parts[-1]
    finally:
        tracker.mark_finished()
        speaker.cancel_fillers()

    proc.wait()
    stderr_thread.join(timeout=2)

    if proc.returncode != 0:
        err = "".join(stderr_chunks).strip()
        print(f"[hata] claude CLI (kod {proc.returncode}): {err}", file=sys.stderr)
        if not first_token_received:
            speaker.say("Claude komutunda bir hata oldu, terminale bak.")

    if buffer.strip():
        speaker.say(clean_for_speech(buffer))

    return "".join(full_text_parts).strip()


# ---------------------------------------------------------------------- main


def main() -> None:
    # Konuşmacı tanıma yüklemesi EN BAŞTA ve ARKA PLANDA başlasın.
    # Torch'un ilk çağrısı sabit ~1.7s ısınma istiyor (ses uzunluğundan
    # bağımsız, kısaltılamıyor). Whisper/TTS yüklemesi de saniyeler sürdüğü
    # için hepsi paralel: açılış süresi toplam yerine EN UZUN olan kadar.
    verifier_box: dict = {}
    verifier_thread = None

    if SPEAKER_VERIFY:
        # Dosya kontrolünü önden yap: yoksa 10 saniye bekleyip hata vermeyelim.
        if not VOICEPRINT_PATH.exists():
            sys.exit(
                f"Ses parmak izi bulunamadı: {VOICEPRINT_PATH}\n"
                f"Önce şunu çalıştır:  python enroll_voice.py\n"
                f"(ya da hands_free.py içinde SPEAKER_VERIFY = False yap)"
            )

        def _init_verifier():
            try:
                verifier_box["value"] = SpeakerVerifier()
            except Exception as exc:  # noqa: BLE001
                verifier_box["error"] = exc

        print("Konuşmacı tanıma arka planda yükleniyor...")
        verifier_thread = threading.Thread(target=_init_verifier, daemon=True)
        verifier_thread.start()

    print(f"TTS motoru: {TTS_ENGINE}")
    backend = make_tts_backend()

    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    print("Whisper yükleniyor...")
    whisper = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")

    speaker = Speaker(backend)

    print("Sesler hazırlanıyor (tek seferlik)...")
    cached_fillers = [(p, backend.synth(p)) for p in FILLER_PHRASES]
    cached_ack = backend.synth(WAKE_ACK)
    cached_sleep_ack = backend.synth(SLEEP_ACK)

    verifier = None
    if verifier_thread is not None:
        verifier_thread.join()
        if "error" in verifier_box:
            raise verifier_box["error"]
        verifier = verifier_box["value"]
        print(f"  ✓ konuşmacı tanıma hazır (eşik {SPEAKER_THRESHOLD})")

    wake_hint = f"{WAKE_WORDS[0].capitalize()} uyan" if REQUIRE_WAKE_VERB else WAKE_WORDS[0].capitalize()
    print(f"Hazır. Uyandırmak için '{wake_hint}' de. Çıkmak için Ctrl+C.\n")

    if UI_ENABLED and _ui_bridge is not None:
        ui_url = _ui_bridge.start()
        print(f"🖥️  Bexi uygulama köprüsü: {ui_url}\n")
        ui_emit("state", value="sleeping")

    is_first_turn = True
    turn_count = 0
    awake = False
    last_interaction = 0.0
    last_topic: str | None = None  # "unut gitsin" için son konuşulan konu

    # --- Misafir ses protokolu durumu ---
    # SES vektorleri SADECE RAM (diske asla yazilmaz), konusma bitince silinir.
    # Misafir ISIMLERI ise (SADECE isim, icerik degil) diskte kalici -
    # Kaan'in kurali: "sadece isimlerini hatirla, naber de".
    greeted_guests: list[np.ndarray] = []   # bu konusmada selamlanmis sesler
    approved_guests: list[np.ndarray] = []  # Kaan onayli 2. sesler
    pending_guest: np.ndarray | None = None  # son selamlanan, onay bekleyen
    had_guest_before = False  # surec boyunca en az bir misafir onaylanip silindi mi
    known_guest_names: set[str] = load_guest_names()

    def remember_guest_name(text: str) -> None:
        name = extract_guest_name(text)
        if name and name not in known_guest_names:
            known_guest_names.add(name)
            save_guest_names(known_guest_names)
            print(f"📝 Misafir ismi hatırlandı: {name} (sadece isim)")

    def reset_guests() -> None:
        """Konusma bitince (uyku) misafir SESLERINI sil - guvenlik geregi.
        Isimler silinmez (Kaan: 'sadece isimlerini hatirla')."""
        nonlocal pending_guest, had_guest_before
        if approved_guests:
            had_guest_before = True
            print("🧹 Misafir sesleri silindi (konuşma bitti). İsimler kalıcı.")
        greeted_guests.clear()
        approved_guests.clear()
        pending_guest = None

    def handle_guest(audio: np.ndarray, text: str) -> None:
        """Sahibi olmayan bir ses Bexi'ye seslendi - protokolu islet."""
        nonlocal pending_guest
        if not GUEST_PROTOCOL or verifier is None:
            return
        if not mentions_bexi(text):
            return  # Bexi'ye seslenmemis - sessizce yok say (eski davranis)
        emb = verifier.embedding(audio)
        if emb is None:
            return  # cok kisa, guvenilir vektor yok
        if guest_best_score(emb, greeted_guests) >= GUEST_MATCH_THRESHOLD:
            return  # bu sese bu konusmada zaten cevap verildi - 1 kez kurali
        greeted_guests.append(emb)
        pending_guest = emb

        # Misafir kendini tanittiysa ismi hatirla + tanidik ismi sicak selamla
        name = extract_guest_name(text)
        if name:
            returning = name in known_guest_names
            remember_guest_name(text)
        else:
            returning = False

        speaker.start_turn()
        if returning:
            # Tanidik isim: once sicak selam, sonra guvenlik acikligini baştan soyle
            speaker.say(f"Naber {name}.")
            speaker.say(GUEST_MEMORY_DISCLOSURE)
        else:
            speaker.say(GUEST_DELETED_EXPLANATION if had_guest_before else GUEST_GREETING)
            speaker.say(GUEST_MEMORY_DISCLOSURE)
        speaker.wait_until_done()

    try:
        while True:
            # ---------------- UYKU MODU ----------------
            if not awake:
                kind, audio = listen_for_trigger(vad)

                if kind == "snap":
                    print("👏 Şıklatma algılandı.")
                    ui_emit("state", value="listening")
                    awake = True
                    last_interaction = time.monotonic()
                    speaker.start_turn()
                    speaker.say(WAKE_ACK, cached=cached_ack)
                    speaker.wait_until_done()
                    continue

                if audio is None or len(audio) < SAMPLE_RATE * 0.3:
                    continue
                text, is_owner, score = transcribe_and_verify(audio, whisper, verifier)
                if not text:
                    continue

                matched, remainder = match_wake_word(text)
                if not matched:
                    # Uyandırma kelimesi yok. Ama sahibi olmayan biri Bexi'ye
                    # ADIYLA seslendiyse (soru sorduysa) misafir protokolu -
                    # yine de UYANMAZ, sadece sinir cumlesini soyler.
                    if not is_owner and mentions_bexi(text):
                        handle_guest(audio, text)
                    else:
                        print(f"   (yok sayıldı: {text})")
                    continue

                if not is_owner:
                    # 'Bexi uyan' dedi ama Kaan'in sesi degil -> misafir
                    # protokolu, uyanmaz.
                    handle_guest(audio, text)
                    continue
                if score is not None:
                    print(f"   ✓ ses doğrulandı ({score:.3f})")

                print(f"👂 Uyandım. ({text})")
                ui_emit("state", value="listening")
                awake = True
                last_interaction = time.monotonic()

                if not remainder:
                    # Sadece 'Bexi' dedi, komut yok -> onay verip dinlemeye geç
                    speaker.start_turn()
                    speaker.say(WAKE_ACK, cached=cached_ack)
                    speaker.wait_until_done()
                    continue

                text = remainder  # 'Bexi, şu dosyayı oku' -> komutu al

            # ---------------- UYANIK MOD ----------------
            else:
                remaining = ACTIVE_WINDOW_SECONDS - (time.monotonic() - last_interaction)
                if remaining <= 0:
                    print("😴 Uzun süre sessizlik, uykuya dönüyorum.")
                    ui_emit("state", value="sleeping")
                    reset_guests()
                    awake = False
                    continue

                # Kalan süreyi timeout olarak veriyoruz: bu süre içinde hiç
                # konuşmazsan None döner ve uykuya geçeriz.
                audio = record_until_silence(vad, timeout=remaining)
                if audio is None:
                    print("😴 Uzun süre sessizlik, uykuya dönüyorum.")
                    ui_emit("state", value="sleeping")
                    reset_guests()
                    awake = False
                    continue
                if len(audio) < SAMPLE_RATE * 0.3:
                    continue
                text, is_owner, score = transcribe_and_verify(
                    audio, whisper, verifier if VERIFY_EVERY_UTTERANCE else None
                )
                if not text:
                    continue

                if not is_owner:
                    # Kaan onayli 2. ses mi? (bu konusma icin gecici) -> izin
                    emb_guest = verifier.embedding(audio) if verifier else None
                    if emb_guest is not None and guest_best_score(
                        emb_guest, approved_guests
                    ) >= GUEST_MATCH_THRESHOLD:
                        remember_guest_name(text)  # tanistiysa ismini hatirla
                        # onayli misafir -> asagi ak, normal islensin
                    else:
                        # Onaysiz farkli ses -> Bexi'ye seslendiyse protokol
                        handle_guest(audio, text)
                        last_interaction = time.monotonic()
                        continue
                elif pending_guest is not None and is_guest_approval(text):
                    # Kaan misafiri onayladi -> 2. ses olarak (RAM'de) kaydet
                    approved_guests.append(pending_guest)
                    pending_guest = None
                    print("🤝 Misafir Kaan onayıyla kaydedildi (geçici).")
                    speaker.start_turn()
                    speaker.say(GUEST_APPROVED_ACK)
                    speaker.wait_until_done()
                    last_interaction = time.monotonic()
                    continue

                # Unutma emri
                if is_forget_command(text):
                    if not last_topic:
                        speaker.start_turn()
                        speaker.say("Unutacak bir şey yok.")
                        speaker.wait_until_done()
                        continue

                    question = (
                        f"Son konuştuğumuz {summarize_topic(last_topic)} "
                        f"konusunu mu unutayım?"
                    )
                    print(f"❓ {question}")
                    speaker.start_turn()
                    speaker.say(question)
                    speaker.wait_until_done()

                    answer = None
                    confirm_audio = record_until_silence(
                        vad, timeout=CONFIRM_TIMEOUT_SECONDS
                    )
                    if confirm_audio is not None:
                        ctext, cowner, _ = transcribe_and_verify(
                            confirm_audio,
                            whisper,
                            verifier if VERIFY_EVERY_UTTERANCE else None,
                        )
                        if cowner:
                            print(f"🗣️  Sen: {ctext}")
                            answer = classify_yes_no(ctext)

                    if answer is not True:
                        speaker.start_turn()
                        speaker.say("Tamam, dokunmuyorum.")
                        speaker.wait_until_done()
                        last_interaction = time.monotonic()
                        continue

                    # Onaylandı -> Claude'a görmezden gelme talimatı gönder
                    text = FORGET_INSTRUCTION.format(topic=last_topic)
                    last_topic = None
                    print("🧹 Unutma talimatı gönderiliyor...")

                    speaker.start_turn()
                    response = ask_claude_code_streaming(
                        text, is_first_turn, speaker
                    )
                    is_first_turn = False
                    turn_count += 1
                    print(f"🤖 Claude: {response}")
                    speaker.wait_until_done()
                    last_interaction = time.monotonic()
                    continue

                # Uyku emri ham metinde kontrol edilir ("Bexi uyu")
                if is_sleep_command(text):
                    print("😴 Uykuya geçiyorum.")
                    ui_emit("state", value="sleeping")
                    reset_guests()
                    speaker.start_turn()
                    speaker.say(SLEEP_ACK, cached=cached_sleep_ack)
                    speaker.wait_until_done()
                    awake = False
                    continue

                # Uyanıkken de "Bexi uyan, ..." diyebilir; varsa ayıkla
                matched, remainder = match_wake_word(text)
                if matched:
                    text = remainder or text

                if not text:
                    continue

            print(f"🗣️  Sen: {text}")
            last_interaction = time.monotonic()

            if MAX_TURNS_PER_SESSION and turn_count >= MAX_TURNS_PER_SESSION:
                print("[bilgi] Context sınırı, yeni oturum başlatılıyor.")
                is_first_turn = True
                turn_count = 0

            speaker.start_turn()
            phrase, cached = random.choice(cached_fillers)
            speaker.say(phrase, is_filler=True, cached=cached)

            last_topic = text  # "unut gitsin" bunu referans alacak

            response = ask_claude_code_streaming(text, is_first_turn, speaker)
            is_first_turn = False
            turn_count += 1
            print(f"🤖 Claude: {response}")

            # Mikrofonu açmadan önce konuşma bitsin (yoksa kendi sesini kaydeder)
            speaker.wait_until_done()
            last_interaction = time.monotonic()

    except KeyboardInterrupt:
        print("\nGörüşürüz.")
    finally:
        speaker.shutdown()


if __name__ == "__main__":
    main()