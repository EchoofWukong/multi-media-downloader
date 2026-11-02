# -*- coding: utf-8 -*-
import json
import os
import glob
import re
import unicodedata

FAVORILER_DOSYASI = "favoriler.json"
VERITABANI_DOSYASI = "isim_veritabani.json"

def ozel_veri_yukle():
    veriler = {}
    if os.path.exists(FAVORILER_DOSYASI):
        with open(FAVORILER_DOSYASI, "r", encoding="utf-8") as f:
            raw = json.load(f)
            for k, v in raw.items():
                # Eski sürümden kalan verileri yeni sisteme uydurur
                is_fav = v.get("is_fav", True if "is_fav" not in v else False)
                veriler[k] = {"username": v.get("username", k), "full_name": v.get("full_name", ""), "is_fav": is_fav, "not": v.get("not", "")}
    return veriler

def ozel_veri_kaydet(uname, fname, is_fav, note):
    veriler = ozel_veri_yukle()
    
    # Eğer adam favori değilse VE notu da yoksa veritabanından tamamen sil
    if not is_fav and not note.strip():
        if uname in veriler: del veriler[uname]
    else:
        veriler[uname] = {"username": uname, "full_name": fname, "is_fav": is_fav, "not": note}
        
    with open(FAVORILER_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)

def ortak_hesaplari_cikar():
    harita = {}
    for dosya in glob.glob("*.json"):
        if dosya in ["isim_veritabani.json", "favoriler.json", "veri.json"]: continue
        hesap_adi = dosya.replace(".json", "")
        try:
            with open(dosya, "r", encoding="utf-8") as f:
                veri = json.load(f)
                for k in veri.get("users", []):
                    uname = k["username"]
                    if uname not in harita: harita[uname] = []
                    if hesap_adi not in harita[uname]: harita[uname].append(hesap_adi)
        except: continue
    return harita

# --- Cinsiyet Motoru ---
KADIN_EMOJILER = ["🎀", "🌸", "💅", "💄", "🧚‍♀️", "🍓", "🦋", "✨", "🤍", "🧸", "🩰", "🐈‍⬛", "👸", "👑"]
ERKEK_EMOJILER = ["🔫", "🕊️", "🦅", "🐺", "🚬", "⛓️", "🦁", "⚔️", "🏴‍☠️", "🦍", "💪", "🤴"]

KADIN_ISIMLER = set()
ERKEK_ISIMLER = set()

if os.path.exists(VERITABANI_DOSYASI):
    with open(VERITABANI_DOSYASI, "r", encoding="utf-8") as f:
        db = json.load(f)
        KADIN_ISIMLER.update(db.get("kadin", []))
        KADIN_ISIMLER.update(db.get("kadin_eksik", [])) 
        ERKEK_ISIMLER.update(db.get("erkek", []))
        ERKEK_ISIMLER.update(db.get("erkek_eksik", []))

def turkce_karakter_temizle(metin): return metin.translate(str.maketrans("ıöüşğç", "iousgc"))
def harf_tekrarlarini_sil(metin): return re.sub(r'(.)\1+', r'\1', metin)
def normalize_kelime(kelime): return harf_tekrarlarini_sil(turkce_karakter_temizle(kelime))
def sesli_harfleri_sil(kelime): return "".join([h for h in kelime if h not in "aeıioöuü"])

KADIN_ISIMLER_NORM = {normalize_kelime(isim) for isim in KADIN_ISIMLER}
ERKEK_ISIMLER_NORM = {normalize_kelime(isim) for isim in ERKEK_ISIMLER}
KADIN_KISALTMALAR = {sesli_harfleri_sil(i): i for i in KADIN_ISIMLER_NORM if len(sesli_harfleri_sil(i)) >= 3}
ERKEK_KISALTMALAR = {sesli_harfleri_sil(i): i for i in ERKEK_ISIMLER_NORM if len(sesli_harfleri_sil(i)) >= 3}

def cinsiyet_analizi(kullanici_adi, tam_isim):
    analiz_metni = unicodedata.normalize('NFKC', str(f"{kullanici_adi} {tam_isim}")).lower()
    if not analiz_metni.strip(): return "Belirsiz", 0
    
    k_skor, e_skor = 0, 0
    for emoji in KADIN_EMOJILER:
        if emoji in analiz_metni: k_skor += 2
    for emoji in ERKEK_EMOJILER:
        if emoji in analiz_metni: e_skor += 2
        
    if k_skor > e_skor: return "Kadın", 95
    if e_skor > k_skor: return "Erkek", 95

    temiz_metin = re.sub(r'[\d_\W]+', ' ', analiz_metni)
    temiz_metin = harf_tekrarlarini_sil(temiz_metin)
    
    for kelime in temiz_metin.split():
        if len(kelime) < 3 and kelime not in ["su", "ay", "nur", "can", "ali", "eda", "ece", "oya"]: continue
        k_norm = turkce_karakter_temizle(kelime)
        if k_norm in KADIN_ISIMLER_NORM: return "Kadın", 90
        if k_norm in ERKEK_ISIMLER_NORM: return "Erkek", 90
        
        if len(k_norm) >= 5:
            for k in KADIN_ISIMLER_NORM:
                if len(k) >= 4 and k in k_norm: return "Kadın", 85
            for e in ERKEK_ISIMLER_NORM:
                if len(e) >= 4 and e in k_norm: return "Erkek", 85

        sessiz = sesli_harfleri_sil(k_norm)
        if len(sessiz) >= 3:
            if sessiz in KADIN_KISALTMALAR: return "Kadın", 80
            if sessiz in ERKEK_KISALTMALAR: return "Erkek", 80
            if len(sessiz) >= 4:
                for k in KADIN_KISALTMALAR:
                    if len(k) >= 3 and k in sessiz: return "Kadın", 75
                for e in ERKEK_KISALTMALAR:
                    if len(e) >= 3 and e in sessiz: return "Erkek", 75
    return "Belirsiz", 50