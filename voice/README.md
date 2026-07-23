# Bexi — Claude Code için sesli arayüz

Terminaldeki **gerçek Claude Code**'a sesle konuşup sesle cevap alırsın.
Ayrı bir sohbet botu değil — `claude` CLI'ı sarmalar, yani Claude dosya
okur, komut çalıştırır, kod yazar, tüm araçları çalışır.

```
"Bexi uyan"  →  konuş  →  Claude çalışır  →  cevabı sesli duyarsın
                                          →  "Bexi uyu" / 10 dk sessizlik
```

**Ne lokal, ne değil:**

| Bileşen | Nerede çalışıyor |
|---|---|
| Sessizlik algılama (VAD) | Lokal |
| Konuşma → metin (Whisper) | Lokal |
| Konuşmacı tanıma (Resemblyzer) | Lokal |
| Metin → konuşma (Piper) | Lokal |
| **Claude'un kendisi** | **Anthropic API** |

Yani internete sadece Claude çağrısı gidiyor. Uyku modunda sıfır token
harcanır.

---

# 1. Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `hands_free.py` | Ana program. Bunu çalıştırıyorsun. |
| `enroll_voice.py` | Sesini tanıtma ve eşik kalibrasyonu. Kurulumda bir kere. |
| `requirements-hands-free.txt` | Python bağımlılıkları |
| `README.md` | Bu dosya |

---

# 2. Kurulum (sırayla)

## 2.1 Klasör

Claude'un üzerinde çalışmasını istediğin **proje dizinine** koy. Önemli:
`claude -p` bulunduğu dizinde çalışır, yani script nerede çalışırsa Claude
oradaki dosyaları görür.

```bash
cd ~/projeler/ark
mkdir voice && cd voice
# 4 dosyayı buraya kopyala
```

## 2.2 Sistem ses kütüphanesi

`sounddevice` bunsuz kurulmaz.

```bash
# macOS
brew install portaudio

# Ubuntu / Debian
sudo apt install portaudio19-dev python3-dev
```

## 2.3 Python ortamı

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-hands-free.txt
```

> **Neden `setuptools<81` pinli?** `webrtcvad` paketi `pkg_resources`'ı
> import ediyor, ama setuptools 81 ile `pkg_resources` kaldırıldı. Pin
> olmadan `ModuleNotFoundError: No module named 'pkg_resources'` alırsın.

## 2.4 Türkçe ses modeli (Piper)

```bash
python -m piper.download_voices tr_TR-fettah-medium
```

Model `~/.local/share/piper/tr_TR-fettah-medium.onnx` yoluna inmeli. Başka
yere inerse `hands_free.py` içindeki `PIPER_MODEL_PATH`'i düzelt.

Diğer Türkçe sesler: `python -m piper.download_voices --list | grep tr_TR`

## 2.5 Claude Code kontrolü

```bash
claude --version
```

Çıktı vermiyorsa önce Claude Code'u kurup login olman gerek.

> `--include-partial-messages` görece yeni bir flag. Tanınmadığına dair hata
> alırsan `claude update` çalıştır.

## 2.6 Sesini tanıt

```bash
python enroll_voice.py
```

5 kez konuşturur, ortalama bir ses parmak izi çıkarıp
`~/.config/bexi/voiceprint.npy` dosyasına kaydeder. Sonunda sana uygun eşiği
önerir — o değeri `hands_free.py` içindeki `SPEAKER_THRESHOLD`'a yaz.

## 2.7 Eşiği doğrula

```bash
python enroll_voice.py --test
```

Konuşan herkesin benzerlik skorunu canlı yazar. **Başkasının sesiyle mutlaka
dene** — onun skoru eşiğin altında kalmalı. Kalmıyorsa eşiği yükselt.

## 2.8 Çalıştır

```bash
python hands_free.py
```

Çıkmak için `Ctrl+C`.

---

# 3. Kullanım

## 3.1 Uyandırma

Uyku modunda mikrofon açıktır ama **hiçbir şey Claude'a gitmez** (token
harcanmaz). Uyanmanın tek yolu:

```
Bexi uyan
```

Komutu aynı cümlede de verebilirsin:

```
Bexi uyan, git status çalıştır
```

Uyandırma ifadesi ayıklanır, Claude'a sadece `git status çalıştır` gider.
Tek başına "Bexi uyan" dersen "Efendim?" der, sonra komutunu söylersin.

## 3.2 Uyanıkken

Wake word tekrar gerekmez, arka arkaya konuşursun. Uykuya iki şekilde döner:

| Yol | Açıklama |
|---|---|
| `Bexi uyu` | "Tamam, uyuyorum." der |
| 10 dakika sessizlik | `ACTIVE_WINDOW_SECONDS = 600`. Her konuşmanda sayaç sıfırlanır. |

Uyku emri de "Bexi" gerektirir. Bu sayede *"şu dosyayı kapat"*, *"portu
kapat ve yeniden başlat"* gibi gerçek komutlar yanlışlıkla uyku emri
sanılmaz — normal komut olarak Claude'a gider.

## 3.3 Unutma komutu

```
Sen:    unut gitsin
Bexi:   Son konuştuğumuz "şu migration mantığını açıkla bana..."
        konusunu mu unutayım?
Sen:    evet
Bexi:   (Claude'a görmezden gelme talimatı gönderir)
```

"hayır" / "iptal" / "vazgeçtim" dersen dokunmaz. Cevabı anlamazsa da
dokunmaz — güvenli taraf.

Kabul edilen kalıplar: *unut gitsin, unut bunu, bunu unut, sil gitsin,
Bexi unut*. Cümlenin tamamı unutma emri olmalı, böylece *"şu satırı unut"*
veya *"geçmiş migration'ları unut ve yeniden oluştur"* gibi gerçek komutlar
tetiklemez.

> **Sınır:** bu **davranışsal** unutma. `claude -p` oturumdan bir parçayı
> cerrahi olarak silmeye izin vermiyor; token'lar context'te kalır. Yapılan
> şey Claude'a "bu konuyu tamamen görmezden gel, bir daha referans verme,
> kalıcı hafıza notlarından da sil" talimatı göndermek. Asıl kalıcı etki
> senin hafıza skill'inin o notu silmesiyle olur.

Neyin unutulacağı **son komutuna** göre belirlenir. Konu birkaç tura
yayıldıysa Claude kapsamı semantik olarak kendisi genişletir.

## 3.4 Uzun süren işler

7 saniyeyi geçen turlarda Claude'un o an ne yaptığını sesli anlatır:
*"bir dosya okuyorum"*, *"web'de araştırıyorum"*, *"bir komut
çalıştırıyorum"*. Cevap gelene kadar ~7 saniyede bir günceller, tekrarda
"Hâlâ ..." diye önek koyar.

Bu bilgi stream'deki `tool_use` olaylarından geliyor. `TOOL_NARRATIONS`
sözlüğünde olmayan bir araç gelirse "{araç adı} kullanıyorum" der — kendi
MCP araçlarının Türkçe karşılıklarını oraya ekleyebilirsin.

---

# 4. Nasıl çalışıyor

```
        ┌─ UYKU ─────────────────────────────────┐
        │  mikrofon açık, Claude'a hiçbir şey    │
        │  gitmiyor                              │
        └──────────────┬─────────────────────────┘
                       │  "Bexi uyan" + ses doğrulandı
                       ▼
   konuş ──► VAD (1 sn sessizlik) ──► kayıt kesilir
                       │
              ┌────────┴────────┐   ← paralel
              ▼                 ▼
        Whisper (STT)    Konuşmacı doğrulama
              └────────┬────────┘
                       ▼
              claude -p --output-format stream-json
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   dolgu sesi     tool_use →      text_delta →
   (anında)       "dosya          cümle bitince
                  okuyorum"       hemen seslendir
                       │
                       ▼
              text_q → [sentez] → audio_q → [çalma]
                       (paralel iki aşama)
```

## Gecikmeyi gizleyen üç mekanizma

**1. Dolgu sesi.** Sıra Claude'a geçer geçmez önceden sentezlenmiş bir
cümle çalınır ("bir saniye düşüneyim"). İlk gerçek token gelince kesilir.
Başlangıçta bir kere sentezlendiği için oynatma anı sıfır gecikmeli.

**2. Cümle cümle streaming.** `--include-partial-messages` ile token akışı
izlenir. Cevabın tamamı beklenmez; bir cümle noktalama ile biter bitmez
seslendirme kuyruğuna girer.

**3. Sentez/çalma paralelliği.** Cümle N çalarken N+1 arka planda
sentezlenir. Sadece ilk cümle gecikme hissettirir.

Ölçüm (5 cümle, 0.4 sn çalma süresi, mock backend):

| Sentez süresi | Seri (eski) | Paralel (yeni) |
|---|---|---|
| 0.8 sn (yavaş/ağ) | 6.00 sn | 4.41 sn |
| 0.15 sn (Piper gibi) | 2.75 sn | **2.17 sn** — ilk ses 0.15 sn'de |

Kritik nokta: sentez çalmadan **yavaşsa** prefetch gecikmeyi tam gizleyemez
(sentez darboğaz olur). Piper gerçek zamandan hızlı olduğu için 2. cümleden
sonrası tamamen gizlenir. Ağ tabanlı motorlar (Edge, ElevenLabs) bu yüzden
daha kötü.

---

# 5. Uçtan uca gecikme

Sen sustuktan sonra ilk sesi duyana kadar:

| Aşama | Süre |
|---|---|
| Sessizlik algılama (`SILENCE_TIMEOUT_MS`) | 1000 ms |
| Whisper transkripsiyon | ~300–800 ms (tahmin) |
| Konuşmacı doğrulama | ~1 ms (Whisper'a paralel) |
| Dolgu sesi (önbellekli) | ~0 ms |
| **Toplam** | **~1.3–1.8 sn** |

Sonra Claude'un asıl cevabı: + ilk token süresi (ağ, 1–3 sn) + Piper ilk
cümle (~150 ms).

**En büyük tek kalem sessizlik beklemesi.** `SILENCE_TIMEOUT_MS = 1000`
rahat bir değer — cümle ortasında duraksasan bile seni kesmez. Daha hızlı
tepki istersen 400-500'e çekebilirsin. 200 ve altına inersen doğal konuşma
duraklamalarında seni yarıda keser; belirtisi terminalde `🗣️ Sen:`
satırında cümlenin yarısını görmendir.

> `enroll_voice.py` içinde bu değer bilerek **800 ms** bırakıldı. Kayıtta
> hız değil doğruluk önemli; yarım kalmış örnekler parmak izini bozar.

---

# 6. Konuşmacı tanıma

`SPEAKER_VERIFY = True` iken başkası "Bexi uyan" dese bile uyanmaz.

Resemblyzer ile sesinden 256 boyutlu bir vektör çıkarılır, kayıtlı parmak
iziyle kosinüs benzerliğine bakılır. Model paketin içinde gelir — internet
gerekmez.

## Ölçümler

Sentetik iki farklı ses üzerinde:

| Durum | Benzerlik |
|---|---|
| Aynı kişi, yeni örnek | 1.000 |
| Farklı kişi | 0.39 – 0.42 |

> **Dürüst uyarı:** bu ölçüm sentetik seslerle yapıldı ve aralarındaki fark
> gerçek insanlardan büyük. Aynı cinsiyetten iki gerçek kişi çok daha yakın
> skor üretir. `--test` ile kendi ortamında kalibre etmen şart — varsayılan
> 0.75'e körlemesine güvenme.

## Ayarlar

| Ayar | Varsayılan | Ne yapar |
|---|---|---|
| `SPEAKER_VERIFY` | `True` | Tamamen kapatmak için `False` |
| `SPEAKER_THRESHOLD` | `0.75` | Eşik. `enroll_voice.py` sana uygun değeri önerir |
| `VERIFY_EVERY_UTTERANCE` | `True` | Uyanıkken gelen her cümleyi de doğrular |
| `SPEAKER_MIN_SECONDS` | `0.6` | Bunun altında güvenilir doğrulama yapılamıyor |
| `ALLOW_SHORT_UNVERIFIED` | `True` | Kısa kayıtlarda ne yapılsın |

**`VERIFY_EVERY_UTTERANCE = True`:** yanındaki biri konuşursa Claude'a
gitmez ve 10 dakikalık sayaç da sıfırlanmaz.

**Kısa ses açığı — bilmen gereken bir taviz:** 0.6 saniyeden kısa
kayıtlarda gömme vektörü güvenilmez oluyor. `ALLOW_SHORT_UNVERIFIED = True`
bunları geçirir, ki senin "evet", "dur" gibi kısa komutların engellenmesin.
Ama bu, başkasının kısa bir sözünün de geçebileceği anlamına gelir. Tam
sıkılık istersen `False` yap; karşılığında kendi kısa komutların da elenir.

## Açılış maliyeti

Torch ilk çağrıda sabit ~1.7 sn ısınma istiyor (ses uzunluğundan bağımsız,
kısaltılamıyor), import ~1.5 sn. Bu yüzden konuşmacı tanıma yüklemesi en
başta arka planda başlatılıp Whisper/TTS yüklemesiyle paralel çalıştırılır:

| | Açılış |
|---|---|
| Seri olsaydı | ~7.4 sn |
| Paralel (mevcut) | ~4.2 sn |

Yani ses tanıma açılışa **sıfır** ekliyor, tamamen gölgede kalıyor.

> **İlk çalıştırma istisnası:** dosyalar disk önbelleğinde olmadığı için ilk
> açılış çok daha uzun sürebilir (ölçümde import tek başına 65 saniye).
> Sonraki açılışlar normale döner. Bir kerelik, panik yapma.

---

# 7. TTS motoru seçimi

`hands_free.py` başındaki `TTS_ENGINE`:

| Motor | Türkçe | Ağ | Ücret | Not |
|---|---|---|---|---|
| **`piper`** (varsayılan) | ✅ | Lokal | Ücretsiz | **Düşük gecikme için bunu kullan.** CPU'da gerçek zamandan hızlı. |
| `elevenlabs` | ✅ | Gerekir | Ücretli | En doğal ses. `eleven_flash_v2_5`. `ELEVENLABS_API_KEY` gerekir. |
| `edge` | ✅ | Gerekir | Ücretsiz | Ağ gecikmesi değişken, yavaş olabilir. |
| `kokoro` | ❌ | Lokal | Ücretsiz | **Türkçe YOK.** Sadece İngilizce. |

## Kendi sesini klonlamak

Mümkün ama gecikmeyi geri verirsin:

- **XTTS-v2** — lokal, Türkçe var, ~6 saniyelik örnekten klonlar. GPU'suz
  yavaş (ilk sese ~2 sn). **Lisans uyarısı:** model ağırlıkları CPML,
  yani ticari kullanıma kapalı. Kendi terminalinde kişisel kullanım sorun
  değil, ama müşteri tarafına taşırsan lisans sorun olur.
- **ElevenLabs** — anında klonlama, ticari olarak temiz. Backend kodda
  hazır; sadece `ELEVEN_VOICE_ID`'ye kendi klonunun id'sini yaz.
- **Piper** — zero-shot klonlama yok. Sıfırdan model eğitmek gerekir
  (saatlerce ses + GPU). Pratik değil.

---

# 8. Ayarlar sözlüğü

`hands_free.py` başında:

### Ses / kayıt
| Ayar | Varsayılan | Açıklama |
|---|---|---|
| `SILENCE_TIMEOUT_MS` | `1000` | Konuşmanın bittiğini varsaymak için sessizlik süresi |
| `VAD_AGGRESSIVENESS` | `2` | 0-3. Yüksek = gürültüyü daha agresif eler |
| `WHISPER_MODEL_SIZE` | `"base"` | `tiny` hızlı/kaba, `small`/`medium` yavaş/doğru |
| `STT_LANGUAGE` | `"tr"` | `None` = otomatik algıla (kısa cümlelerde yanılıyor) |

### Uyandırma
| Ayar | Varsayılan | Açıklama |
|---|---|---|
| `WAKE_WORDS` | `["bexi", ...]` | Whisper'ın ürettiği varyantları buraya ekle |
| `REQUIRE_WAKE_VERB` | `True` | `False` yaparsan tek başına "Bexi" de uyandırır |
| `WAKE_FUZZY_THRESHOLD` | `0.92` | Düşürürsen kolay uyanır, yanlış tetik artar |
| `WAKE_MAX_TOKEN_INDEX` | `2` | Uyandırma kelimesi cümlenin başında olmalı |
| `ACTIVE_WINDOW_SECONDS` | `600` | Sessizlikte uykuya dönme süresi |
| `ENABLE_SNAP` | `False` | Parmak şıklatma ile uyandırma |

### Claude
| Ayar | Varsayılan | Açıklama |
|---|---|---|
| `MAX_TURNS_PER_SESSION` | `0` | `0` = zorla oturum sıfırlama kapalı |
| `LONG_WAIT_THRESHOLD_SECONDS` | `7.0` | Aktivite anlatımının devreye girme eşiği |
| `TOOL_NARRATIONS` | sözlük | Araç adı → Türkçe anlatım |
| `FILLER_PHRASES` | liste | Bekleme dolgu cümleleri |

**`MAX_TURNS_PER_SESSION = 0` neden kapalı:** Claude Code context'i kendi
yönetiyor (otomatik compaction) ve kalıcı hafıza skill'in önemli notları
diske yazıp geri okuyor. Zorla sıfırlama bunların üstüne biner, iş
ortasında gereksiz bağlam kaybettirir. Yine de tavan istersen sayı ver.

Not: dolgu sesi ve streaming **hiç ekstra token yaratmaz** — dolgu Claude'a
hiç gitmez, streaming sadece tokenleri ne zaman aldığını değiştirir.

---

# 9. Sorun giderme

| Belirti | Sebep / Çözüm |
|---|---|
| `OSError: PortAudio library not found` | Adım 2.2 atlanmış. `brew install portaudio` / `apt install portaudio19-dev` |
| `ModuleNotFoundError: pkg_resources` | setuptools 81+ kurulu. `pip install "setuptools<81"` |
| `Piper ses modeli bulunamadı` | Adım 2.4 çalıştırılmamış ya da model başka yola inmiş. `PIPER_MODEL_PATH`'i düzelt |
| `Ses parmak izi bulunamadı` | `python enroll_voice.py` çalıştır, ya da `SPEAKER_VERIFY = False` |
| `--include-partial-messages` tanınmıyor | `claude update` |
| Uyanmıyor | Terminale bak: `(yok sayıldı: ...)` satırı Whisper'ın "Bexi"yi nasıl duyduğunu gösterir. O metni `WAKE_WORDS`'e ekle |
| Kendi sesime uyanmıyor | `SPEAKER_THRESHOLD` yüksek. `enroll_voice.py --test` ile kendi skorunu gör, altına ayarla |
| Başkasının sesine uyanıyor | `SPEAKER_THRESHOLD` düşük. Yükselt |
| Cümlem yarıda kesiliyor | `SILENCE_TIMEOUT_MS` düşük. Yükselt |
| Her turda uzun bekliyorum | `SILENCE_TIMEOUT_MS` yüksek. 400-500'e çek |
| Mikrofon çalışmıyor (macOS) | Sistem Ayarları → Gizlilik → Mikrofon, terminale izin ver |
| Cihazları görmek | `python -c "import sounddevice; print(sounddevice.query_devices())"` |

---

# 10. Güvenlik notu

Script `claude -p` (headless/print modu) kullanıyor. Bu modda Claude Code
dosya değiştirme gibi eylemleri **onay istemeden** yapabilir. Kritik bir
repoda çalışacaksan `ask_claude_code_streaming` içindeki komuta
`--permission-mode` ekleyip kısıtla. Ayarları Claude Code dokümantasyonunda.

---

# 11. Giderilen buglar

Geliştirme sırasında bulunup düzeltilenler — kodu değiştirirken tekrar
üretmemek için:

| Bug | Etki |
|---|---|
| **stderr deadlock** — stdout okunup `proc.wait()` çağrıldıktan *sonra* stderr okunuyordu. Claude 64 KB'dan fazla stderr yazınca boru dolup kalıcı kilitlenme. | Kritik. Sahte binary ile üretilip doğrulandı. Artık stderr ayrı thread'de boşaltılıyor. |
| **Ses cihazı çakışması** — dolgu ayrı thread'den `sd.play()` çağırıyordu. sounddevice tek global çıkış akışı kullandığı için dolgu thread'i Speaker'ın cümlesini `sd.stop()` ile kesebiliyordu. | Kritik. Tüm çalma tek Speaker thread'inden geçiyor. |
| **`wait_until_done()` sonsuz kilit** — TTS bir cümlede hata verirse `task_done()` çağrılmıyor, `q.join()` sonsuza kadar bekliyordu. | Kritik. `try/finally` eklendi. |
| **Sessizlik zaman aşımı hiç çalışmıyordu** — `record_until_silence` konuşma gelene kadar sonsuza kadar blokluyordu, yani "10 dk sessizlikte uyu" asla tetiklenmezdi. | Kritik. Fonksiyona `timeout` eklendi. |
| **Uyku emri yanlış tetikleniyordu** — "cümlede uyku kelimesi geçiyor mu" diye bakıyordu, yani *"şu dosyayı kapat"* komutu uykuya geçiriyordu. | Artık "Bexi" + uyku fiili şartı var. |
| **Sentez ve çalma seriydi** — her cümle tam sentez gecikmesini ayrı ayrı ödüyordu. | İki aşamalı paralel hat kuruldu. |
| **Dolgu her turda yeniden sentezleniyordu** | Başlangıçta bir kere sentezlenip önbelleğe alınıyor. |
| **Türkçe metin İngilizce sesle okunuyordu** | Kokoro'da Türkçe yok. Piper varsayılan yapıldı. |
| **Markdown/kod sesli okunuyordu** | "yıldız yıldız backtick def main" diye okuyordu. `clean_for_speech()` eklendi. |
| **Whisper dil otomatik algılıyordu** | Kısa cümlelerde yanlış dil seçiyordu. `STT_LANGUAGE="tr"` sabitlendi. |
| **`None` skor formatlama çökmesi** | `ALLOW_SHORT_UNVERIFIED = False` yapılınca `TypeError`. `fmt_score()` eklendi. |
| **Konuşmacı doğrulama kritik yoldaydı** | Transkripsiyonla paralelleştirildi, 50 ms → ~1 ms. |
| **Torch ısınması açılışta 30 sn sanılıyordu** | Aslında disk önbelleği etkisiydi. Gerçek ~1.7 sn, o da arka plana alındı. |
| **Watchdog "Hâlâ" mantığı** | Yanlış değişkenle karşılaştırdığı için tekrar tespiti hiç çalışmıyordu. |
| **VAD frame boyutu** | Eksik boyutlu frame gelirse `webrtcvad` exception atıyordu; artık atlanıyor. |
| **Forward reference `NameError`** | `long_wait_watchdog`, `Speaker`'ı tanımlanmadan önce tip ipucu olarak kullanıyordu. `from __future__ import annotations` eklendi. |

---

# 12. Test edilmeyenler

Dürüstlük için: aşağıdakiler gerçek donanımda **denenmedi**, geliştirme
ortamında ses cihazı ve bazı modeller yoktu.

- Mikrofon kaydı ve hoparlör çıkışı (mock ile test edildi, gerçek cihazla değil)
- Piper'ın Türkçe sesi ve gerçek sentez hızı (model indirilemedi)
- Whisper'ın gerçek transkripsiyon süresi (model indirilemedi) — tablodaki
  300-800 ms bir tahmin
- Konuşmacı tanımanın gerçek insan sesleri üzerindeki ayırt ediciliği
  (sentetik seslerle test edildi)
- Parmak şıklatma algılamanın gerçek ortamdaki yanlış tetik oranı

Mantık katmanları (wake word eşleştirme, uyku/unutma emri ayrımı, streaming
parse, deadlock, thread güvenliği, gecikme mimarisi) mock'larla test edildi
ve geçti.

---

# 13. Daha ileri götürmek istersen

| Değişiklik | Kazanç | Bedel |
|---|---|---|
| `WHISPER_MODEL_SIZE = "tiny"` | Daha hızlı transkripsiyon | Doğruluk düşer, gürültüde belirgin |
| Whisper'ı GPU'da çalıştır (`device="cuda"`, `compute_type="float16"`) | STT ~3-5x hızlanır | CUDA'lı GPU gerekir |
| `SILENCE_TIMEOUT_MS` 1000 → 500 | ~500 ms kazanç | Duraksarsan kesilme riski |
| Sesli mod için daha hızlı model (`--model haiku`) | İlk token belirgin düşer | Cevap kalitesi düşer |
| Kalıcı Claude Code oturumu (`--input-format stream-json`, çift yönlü) | Tur başına process başlatma yükü kalkar | Mimari yeniden yazım |
| Barge-in (Claude konuşurken araya girme) | Doğal sohbet hissi | Aynı anda dinleme+çalma yönetimi, orta ölçekli iş |

En yüksek etki/efor oranı: **GPU varsa Whisper'ı GPU'ya taşımak** ve
**`SILENCE_TIMEOUT_MS`'i kendi konuşma ritmine göre ayarlamak**. İkisi de
tek satır.
