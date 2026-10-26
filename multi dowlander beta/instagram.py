import os, re, http.cookiejar, requests
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
                             QLabel, QProgressBar, QFileDialog, QButtonGroup, QApplication, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import yt_dlp
import imageio_ffmpeg

def son_klasoru_al():
    if os.path.exists("son_klasor.txt"):
        with open("son_klasor.txt", "r", encoding="utf-8") as f:
            klasor = f.read().strip()
            if os.path.exists(klasor): return klasor
    return os.path.join(os.path.expanduser("~"), "Desktop")

def son_klasoru_kaydet(klasor):
    with open("son_klasor.txt", "w", encoding="utf-8") as f:
        f.write(klasor)

class IgMotor(QThread):
    ilerleme = pyqtSignal(int, str, str)
    def __init__(self, url, mod, klasor, kalite):
        super().__init__()
        self.url, self.mod, self.klasor, self.kalite = url, mod, klasor, kalite

    def run(self):
        try:
            self.ilerleme.emit(0, "Başlıyor...", "")
            if self.mod == "photo": self.profil_indir()
            else: self.medya_indir(self.mod == "audio")
        except Exception as e:
            self.ilerleme.emit(0, f"Hata: {str(e)[:70]}", "")

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
        opts = {
            "noplaylist": True, 
            "quiet": True, 
            "progress_hooks": [self.hook]
        }
        if os.path.exists("cookies.txt"): opts["cookiefile"] = "cookies.txt"
        
        # Instagram linkindeki gereksiz takip parametrelerini siler
        temiz_url = self.url.split('?')[0]
        
        ffmpeg_var = False
        try:
            ffmpeg_yolu = imageio_ffmpeg.get_ffmpeg_exe()
            if os.path.exists(ffmpeg_yolu):
                opts["ffmpeg_location"] = ffmpeg_yolu
                ffmpeg_var = True
        except:
            pass
        
        if is_mp3:
            # Instagram'da "title" bazen boş döner, o yüzden ID kullanmak daha güvenlidir
            opts["outtmpl"] = os.path.join(self.klasor, "%(uploader)s_%(id)s (Ses).mp3")
            opts["format"] = "bestaudio[ext=m4a]/bestaudio" 
            if ffmpeg_var:
                opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
        else: 
            opts["outtmpl"] = os.path.join(self.klasor, "%(uploader)s_%(id)s (Instagram).mp4")
            # Çözünürlük ne seçilirse seçilsin, Instagram'ın izin verdiği tek parça en iyi dosyayı çeker
            opts["format"] = "best[ext=mp4]/best"
            
        with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([temiz_url])

    def profil_indir(self):
        self.ilerleme.emit(20, "Profil aranıyor...", "")
        user = re.search(r"instagram\.com/([\w.]+)", self.url)
        user = user.group(1) if user else self.url.strip("@")
        
        jar = http.cookiejar.MozillaCookieJar("cookies.txt")
        jar.load(ignore_discard=True, ignore_expires=True)
        s = requests.Session()
        for c in jar: s.cookies.set_cookie(c)
        s.headers.update({"User-Agent": "Mozilla/5.0", "x-ig-app-id": "936619743392459"})
        
        r = s.get(f"https://www.instagram.com/api/v1/users/web_profile_info/?username={user}")
        if r.status_code != 200: raise RuntimeError("Gizli profil veya API engeli")
        
        self.ilerleme.emit(60, "Fotoğraf indiriliyor...", "")
        img = requests.get(r.json()["data"]["user"].get("profile_pic_url_hd")).content
        with open(os.path.join(self.klasor, f"{user}_profil.jpg"), "wb") as f: f.write(img)
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
        self.kalite_kutu.addItems(["En İyi Kalite (Otomatik)", "1080p", "720p", "480p", "360p"])
        self.kalite_kutu.setFixedHeight(44)
        layout.addWidget(self.kalite_kutu)
        layout.addSpacing(15)
        
        self.grup.buttonClicked.connect(self.mod_degisti)
        
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

    def mod_degisti(self, btn):
        if self.btn_video.isChecked():
            self.kalite_kutu.setEnabled(True)
        else:
            self.kalite_kutu.setEnabled(False)

    def klasor_sec(self):
        secilen = QFileDialog.getExistingDirectory(self, "Kayıt Yeri Seç")
        if secilen:
            self.klasor_input.setText(secilen)
            son_klasoru_kaydet(secilen)

    def baslat(self):
        u, k = self.url_input.text().strip(), self.klasor_input.text().strip()
        if not u: return self.lbl_durum.setText("Lütfen link girin!")
        m = "audio" if self.btn_ses.isChecked() else "photo" if self.btn_profil.isChecked() else "video"
        kalite = self.kalite_kutu.currentText()
        
        self.btn_indir.setEnabled(False)
        self.bar.setValue(0)
        self.motor = IgMotor(u, m, k, kalite)
        self.motor.ilerleme.connect(lambda y, t, h: (self.bar.setValue(y), self.lbl_durum.setText(t), self.lbl_hiz.setText(h)))
        self.motor.finished.connect(lambda: self.btn_indir.setEnabled(True))
        self.motor.start()