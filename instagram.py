import os, re, requests
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QLabel, QProgressBar, QFileDialog, QButtonGroup, QApplication, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import yt_dlp
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

KLASOR = os.path.dirname(os.path.abspath(__file__))
COOKIE_DOSYASI = os.path.join(KLASOR, "cookies.txt")
SON_KLASOR_DOSYASI = os.path.join(KLASOR, "son_klasor.txt")

MASAUSTU_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
MOBIL_UA = ("Instagram 275.0.0.27.98 Android (33/13; 420dpi; 1080x2400; samsung; "
            "SM-G991B; o1s; exynos2100; en_US; 458229237)")

# Kullanıcı adı değil, içerik linki olan yollar
ayrilmis_yollar = {"p", "reel", "reels", "stories", "explore", "tv", "accounts", "direct"}

def son_klasoru_al():
    if os.path.exists(SON_KLASOR_DOSYASI):
        with open(SON_KLASOR_DOSYASI, "r", encoding="utf-8") as f:
            klasor = f.read().strip()
            if os.path.exists(klasor):
                return klasor
    return os.path.join(os.path.expanduser("~"), "Desktop")

def son_klasoru_kaydet(klasor):
    with open(SON_KLASOR_DOSYASI, "w", encoding="utf-8") as f:
        f.write(klasor)

def cerez_oku():
    """cookies.txt (Netscape) dosyasından instagram cookie'lerini {isim: değer} olarak okur."""
    cerezler = {}
    if not os.path.exists(COOKIE_DOSYASI):
        return cerezler
    with open(COOKIE_DOSYASI, "r", encoding="utf-8", errors="ignore") as f:
        for satir in f:
            satir = satir.rstrip("\r\n")
            if satir.startswith("#HttpOnly_"):
                satir = satir[len("#HttpOnly_"):]
            elif not satir.strip() or satir.startswith("#"):
                continue
            parca = satir.split("\t")
            if len(parca) < 7:
                parca = satir.split(None, 6)
            if len(parca) >= 7 and "instagram.com" in parca[0]:
                cerezler[parca[5]] = parca[6].strip()
    return cerezler

def kullanici_adi_bul(girdi):
    """Link ya da @isim ya da düz isim -> kullanıcı adı. Bulamazsa None."""
    girdi = girdi.strip()
    m = re.search(r"instagram\.com/([\w.]+)", girdi)
    if m:
        ad = m.group(1)
        return None if ad.lower() in ayrilmis_yollar else ad
    ad = girdi.strip("@").strip("/")
    return ad if re.fullmatch(r"[\w.]+", ad) else None


class IgMotor(QThread):
    ilerleme = pyqtSignal(int, str, str)

    def __init__(self, url, mod, klasor, kalite):
        super().__init__()
        self.url, self.mod, self.klasor, self.kalite = url, mod, klasor, kalite
        self.hatalar = []

    def run(self):
        try:
            self.ilerleme.emit(0, "Başlıyor...", "")
            if not os.path.isdir(self.klasor):
                raise RuntimeError("Kayıt klasörü bulunamadı.")
            if self.mod == "photo":
                self.profil_indir()
            else:
                self.medya_indir(self.mod == "audio")
        except Exception as e:
            print("HATA:", repr(e))
            self.ilerleme.emit(0, f"Hata: {str(e)[:90]}", "")

    # ------------------------------------------------------------------
    # VİDEO / REELS / SES  (yt-dlp)
    # ------------------------------------------------------------------
    def hook(self, d):
        if d["status"] == "downloading":
            t = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            f = d["downloaded_bytes"] / t if t > 0 else 0
            s = d.get("speed")
            h = f"{s / 1048576:.1f} MB/s" if s else ""
            self.ilerleme.emit(int(f * 100), f"İndiriliyor... %{int(f * 100)}", h)
        elif d["status"] == "finished":
            self.ilerleme.emit(100, "Bitti ✔", "")

    def medya_indir(self, is_mp3):
        if "instagram.com" not in self.url:
            raise RuntimeError("Video/ses için Instagram linki gir.")

        opts = {"noplaylist": True, "quiet": True, "progress_hooks": [self.hook]}
        if os.path.exists(COOKIE_DOSYASI):
            opts["cookiefile"] = COOKIE_DOSYASI

        temiz_url = self.url.split("?")[0]

        ffmpeg_var = False
        try:
            ffmpeg_yolu = imageio_ffmpeg.get_ffmpeg_exe()
            if os.path.exists(ffmpeg_yolu):
                opts["ffmpeg_location"] = ffmpeg_yolu
                ffmpeg_var = True
        except Exception:
            pass

        if is_mp3:
            opts["outtmpl"] = os.path.join(self.klasor, "%(uploader)s_%(id)s (Ses).%(ext)s")
            opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
            if ffmpeg_var:
                opts["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                           "preferredcodec": "mp3", "preferredquality": "192"}]
        else:
            opts["outtmpl"] = os.path.join(self.klasor, "%(uploader)s_%(id)s (Instagram).%(ext)s")
            opts["format"] = "best[ext=mp4]/best"

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([temiz_url])

    # ------------------------------------------------------------------
    # PROFİL FOTOĞRAFI  (Playwright Network Interception ile)
    # ------------------------------------------------------------------
    def profil_indir(self):
        user = kullanici_adi_bul(self.url)
        if not user:
            raise RuntimeError("Profil linki veya kullanıcı adı gir.")

        self.ilerleme.emit(15, "Gizli tarayıcı başlatılıyor...", "")
        img_url = None

        # 1. Eski çerez sistemini Playwright formatına çeviriyoruz
        cerez_dict = cerez_oku() 
        playwright_cookies = []
        for isim, deger in cerez_dict.items():
            playwright_cookies.append({
                "name": isim,
                "value": deger,
                "domain": ".instagram.com",
                "path": "/"
            })

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            context = browser.new_context(
                user_agent=MASAUSTU_UA,
                viewport={"width": 1280, "height": 800}
            )
            
            # 2. Çerezleri tarayıcıya ekle
            if playwright_cookies:
                context.add_cookies(playwright_cookies)
                self.ilerleme.emit(25, f"{len(playwright_cookies)} adet çerez tarayıcıya yüklendi.", "")
            else:
                self.ilerleme.emit(25, "Çerez bulunamadı, misafir modunda deneniyor...", "")

            page = context.new_page()

            def handle_response(response):
                nonlocal img_url
                url = response.url
                if ("/graphql" in url or "/api/v1/" in url) and response.request.resource_type in ["fetch", "xhr"]:
                    try:
                        json_data = response.json()
                        if "data" in json_data and "user" in json_data["data"]:
                            u = json_data["data"]["user"]
                            if u.get("username", "").lower() == user.lower():
                                img_url = u.get("hd_profile_pic_url_info", {}).get("url") or u.get("profile_pic_url_hd") or u.get("profile_pic_url")
                        elif "user" in json_data and "hd_profile_pic_url_info" in json_data["user"]:
                            u = json_data["user"]
                            img_url = u.get("hd_profile_pic_url_info", {}).get("url")
                    except Exception:
                        pass

            page.on("response", handle_response)
            self.ilerleme.emit(40, f"@{user} profiline gidiliyor ve ağ dinleniyor...", "")
            
            try:
                page.goto(f"https://www.instagram.com/{user}/", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(4000)
            except Exception as e:
                self.hatalar.append(f"Tarayıcı hatası: {str(e)}")

            browser.close()

        if not img_url:
            raise RuntimeError(f"Profil fotoğrafı ağ trafiğinden yakalanamadı. Hesap kısıtlı olabilir veya çerez eksik.")

        self.ilerleme.emit(70, "HD Fotoğraf yakalandı, indiriliyor...", "")
        r = requests.get(img_url, headers={"User-Agent": MASAUSTU_UA}, timeout=20)
        
        if r.status_code != 200 or not r.content:
            raise RuntimeError(f"Fotoğraf indirilemedi (HTTP {r.status_code}).")

        yol = os.path.join(self.klasor, f"{user}_profil.jpg")
        with open(yol, "wb") as f:
            f.write(r.content)
            
        print("Kaydedildi:", yol, f"({len(r.content) // 1024} KB)")
        self.ilerleme.emit(100, "Kaydedildi ✔", "")


class InstagramSayfasi(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)

        self.setStyleSheet("""
            QComboBox { background-color: #0f1424; border: 2px solid #2a3050; border-radius: 10px; padding: 10px; color: #ffffff; font-size: 14px; font-weight: bold; }
            QComboBox:focus { border: 2px solid #6b8aff; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #151b2d; color: #ffffff; selection-background-color: #1b2a5e; }
        """)

        baslik = QLabel("Instagram İndirme Araçları")
        baslik.setProperty("class", "baslik")
        layout.addWidget(baslik)

        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Link veya Kullanıcı Adı Girin...")
        self.url_input.setFixedHeight(48)
        btn_yapistir = QPushButton("Yapıştır")
        btn_yapistir.setProperty("class", "normal")
        btn_yapistir.setFixedSize(100, 48)
        btn_yapistir.clicked.connect(lambda: self.url_input.setText(QApplication.clipboard().text()))
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(btn_yapistir)
        layout.addLayout(url_layout)
        layout.addSpacing(15)

        self.grup = QButtonGroup(self)
        kart_layout = QHBoxLayout()
        self.btn_video = QPushButton("Video / Reels\nmp4")
        self.btn_ses = QPushButton("Ses\nmp3")
        self.btn_profil = QPushButton("Profil\nFotoğrafı")

        for idx, btn in enumerate([self.btn_video, self.btn_ses, self.btn_profil]):
            btn.setProperty("class", "kart")
            btn.setFixedHeight(75)
            btn.setCheckable(True)
            self.grup.addButton(btn, idx)
            kart_layout.addWidget(btn)
        self.btn_video.setChecked(True)
        layout.addLayout(kart_layout)
        layout.addSpacing(10)

        self.kalite_kutu = QComboBox()
        self.kalite_kutu.addItems(["En İyi Kalite (Otomatik)"])
        self.kalite_kutu.setFixedHeight(44)
        self.kalite_kutu.setEnabled(False) 
        layout.addWidget(self.kalite_kutu)
        layout.addSpacing(15)

        kayit_layout = QHBoxLayout()
        self.klasor_input = QLineEdit()
        self.klasor_input.setText(son_klasoru_al())
        self.klasor_input.setFixedHeight(44)
        btn_klasor = QPushButton("Klasör seç")
        btn_klasor.setProperty("class", "normal")
        btn_klasor.setFixedSize(100, 44)
        btn_klasor.clicked.connect(self.klasor_sec)
        kayit_layout.addWidget(self.klasor_input)
        kayit_layout.addWidget(btn_klasor)
        layout.addLayout(kayit_layout)
        layout.addSpacing(20)

        self.btn_indir = QPushButton("İNDİR")
        self.btn_indir.setProperty("class", "indir_btn")
        self.btn_indir.setFixedHeight(60)
        self.btn_indir.clicked.connect(self.baslat)
        layout.addWidget(self.btn_indir)
        layout.addSpacing(15)

        durum_layout = QHBoxLayout()
        self.lbl_durum = QLabel("Hazır")
        self.lbl_durum.setProperty("class", "alt_metin")
        self.lbl_hiz = QLabel("")
        self.lbl_hiz.setProperty("class", "alt_metin")
        self.lbl_hiz.setAlignment(Qt.AlignRight)
        durum_layout.addWidget(self.lbl_durum)
        durum_layout.addWidget(self.lbl_hiz)

        self.bar = QProgressBar()
        self.bar.setFixedHeight(8)
        layout.addLayout(durum_layout)
        layout.addWidget(self.bar)
        layout.addStretch()

        self.motor = None

    def klasor_sec(self):
        secilen = QFileDialog.getExistingDirectory(self, "Kayıt Yeri Seç")
        if secilen:
            self.klasor_input.setText(secilen)
            son_klasoru_kaydet(secilen)

    def baslat(self):
        u, k = self.url_input.text().strip(), self.klasor_input.text().strip()
        if not u:
            self.lbl_durum.setText("Lütfen link girin!")
            return
        m = "audio" if self.btn_ses.isChecked() else "photo" if self.btn_profil.isChecked() else "video"

        self.btn_indir.setEnabled(False)
        self.bar.setValue(0)
        self.motor = IgMotor(u, m, k, self.kalite_kutu.currentText())
        self.motor.ilerleme.connect(
            lambda y, t, h: (self.bar.setValue(y), self.lbl_durum.setText(t), self.lbl_hiz.setText(h)))
        self.motor.finished.connect(lambda: self.btn_indir.setEnabled(True))
        self.motor.start()