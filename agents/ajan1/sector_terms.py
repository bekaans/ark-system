"""NACE kodu -> Turkce arama terimi eslemesi (Google Maps sorgulari icin)."""

SECTOR_TERMS = {
    "45.1": "oto galeri",
    "47": "magaza",
    "47.1": "market",
    "47.2": "sarkuteri",
    "47.3": "benzin istasyonu",
    "47.4": "elektronik magazasi",
    "47.5": "mobilya magazasi",
    "47.6": "kitapci",
    "47.7": "butik giyim magazasi",
    "47.8": "pazar yeri",
    "47.9": "seyyar satici",
    "55": "otel",
    "55.1": "pansiyon",
    "55.2": "kamp alani",
    "55.3": "karavan parki",
    "55.9": "misafirhane",
    "56": "lokanta",
    "56.1": "restoran",
    "56.3": "kafe bar",
    "74.1": "grafik tasarim ajansi",
    "74.2": "fotografci",
    "93": "spor salonu",
    "96": "kuafor guzellik salonu",
}

CITIES = ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya"]

# s1-7 "surekli-calisan dongu" kapsaminda zaman icinde eklenecek yeni sehirler.
# run_next_batch.py bunlari CITIES'e degil, ayri bir listeye koyar ki ilk 5
# sehirle ilgili gecmis is (scrape_progress'te 'done') bozulmasin.
# Sira TUIK GSYIH (il bazinda ekonomik buyukluk, ticaret hacmi vekili) sirasina
# gore - 2026-07-24, Kaan'in talimatiyla 81 ilin tamami eklendi; run_next_batch.py
# kuyruk bosaldikca bu listeden 5'erli kademeler halinde otomatik acar
# (bkz. seed_next_tier), boylece kademe bitince elle mudahale gerekmez.
CITIES_EXPANSION = [
    # ilk kademe (2026-07-16'da eklendi, tamamlandi)
    "Adana", "Gaziantep", "Konya", "Mersin", "Kayseri",
    "Eskisehir", "Diyarbakir", "Samsun", "Denizli", "Sanliurfa",
    # kalan 66 il, ticaret hacmine (GSYIH) gore sirali - 5'erli kademeler halinde acilir
    "Kocaeli", "Manisa", "Tekirdag", "Hatay", "Balikesir",
    "Sakarya", "Mugla", "Aydin", "Kahramanmaras", "Trabzon",
    "Canakkale", "Afyonkarahisar", "Malatya", "Erzurum", "Sivas",
    "Zonguldak", "Ordu", "Kutahya", "Mardin", "Van",
    "Elazig", "Kirklareli", "Usak", "Corum", "Isparta",
    "Edirne", "Duzce", "Osmaniye", "Tokat", "Bolu",
    "Adiyaman", "Rize", "Aksaray", "Kastamonu", "Yalova",
    "Batman", "Giresun", "Yozgat", "Bilecik", "Sirnak",
    "Amasya", "Kirikkale", "Nigde", "Karaman", "Burdur",
    "Nevsehir", "Karabuk", "Erzincan", "Agri", "Mus",
    "Kirsehir", "Kars", "Siirt", "Bitlis", "Artvin",
    "Bingol", "Cankiri", "Sinop", "Hakkari", "Bartin",
    "Igdir", "Gumushane", "Kilis", "Tunceli", "Ardahan",
    "Bayburt",
]
