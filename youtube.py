import os
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

class YtMotor(QThread):
    ilerleme = pyqtSignal(int, str, str)
    
    def __init__(self, url, is_mp3, klasor, kalite):
        super().__init__()
        self.url, self.is_mp3, self.klasor, self.kalite = url, is_mp3, klasor, kalite

    def run(self):
        try:
            self.ilerleme.emit(0, "Başlıyor...", "")
            self.medya_indir()
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
            self.ilerleme.emit(100, "Dönüştürülüyor...", "")

    def medya_indir(self):
        ffmpeg_yolu = imageio_ffmpeg.get_ffmpeg_exe()
        opts = {
            "noplaylist": True, "quiet": True, 
            "progress_hooks": [self.hook], "ffmpeg_location": ffmpeg_yolu
        }
        if os.path.exists("cookies.txt"): opts["cookiefile"] = "cookies.txt"

        if self.is_mp3:
            # SADECE BURASI DEĞİŞTİ: İsmin sonuna (Ses) ekliyor
            opts["outtmpl"] = os.path.join(self.klasor, "%(uploader)s_%(title).60s (Ses).mp3")
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
        else:
            # SADECE BURASI DEĞİŞTİ: İsmin sonuna seçilen kaliteyi ekliyor
            kalite_etiketi = self.kalite if self.kalite != "En İyi Kalite (Otomatik)" else "Otomatik"
            opts["outtmpl"] = os.path.join(self.klasor, f"%(uploader)s_%(title).60s ({kalite_etiketi}).mp4")
            
            # Kalite Seçimi Mantığı (Senin çalışan kodun, dokunulmadı)
            kalite_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            if self.kalite == "1080p":
                kalite_format = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best"
            elif self.kalite == "720p":
                kalite_format = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"
            elif self.kalite == "480p":
                kalite_format = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best"
            elif self.kalite == "360p":
                kalite_format = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best"
                
            opts["format"] = kalite_format
            
        with yt_dlp.YoutubeDL(opts) as ydl: 
            ydl.download([self.url])
            self.ilerleme.emit(100, "Bitti ✔", "")

class YouTubeSayfasi(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # QComboBox (Açılır Menü) için özel stil
        self.setStyleSheet("""
            QComboBox { background-color: #0f1424; border: 2px solid #2a3050; border-radius: 10px; padding: 10px; color: #ffffff; font-size: 14px; font-weight: bold; }
            QComboBox:focus { border: 2px solid #6b8aff; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #151b2d; color: #ffffff; selection-background-color: #1b2a5e; }
        """)
        
        baslik = QLabel("YouTube İndirme Araçları")
        baslik.setProperty("class", "baslik")
        layout.addWidget(baslik)
        
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube Video veya Shorts Linki Girin...")
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
        
        self.btn_video = QPushButton("Video\nmp4")
        self.btn_ses = QPushButton("Ses\nmp3")
        
        for idx, btn in enumerate([self.btn_video, self.btn_ses]):
            btn.setProperty("class", "kart")
            btn.setFixedHeight(75)
            btn.setCheckable(True)
            self.grup.addButton(btn, idx)
            kart_layout.addWidget(btn)
        
        self.btn_video.setChecked(True)
        layout.addLayout(kart_layout)
        layout.addSpacing(10)
        
        # Kalite Seçici
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
        # Ses seçiliyse kalite seçiciyi kapat
        if self.btn_ses.isChecked():
            self.kalite_kutu.setEnabled(False)
        else:
            self.kalite_kutu.setEnabled(True)

    def klasor_sec(self):
        secilen = QFileDialog.getExistingDirectory(self, "Kayıt Yeri Seç")
        if secilen:
            self.klasor_input.setText(secilen)
            son_klasoru_kaydet(secilen)

    def baslat(self):
        u = self.url_input.text().strip()
        k = self.klasor_input.text().strip()
        
        if not u: 
            self.lbl_durum.setText("Lütfen YouTube linki girin!")
            return
            
        is_mp3 = self.btn_ses.isChecked()
        kalite = self.kalite_kutu.currentText()
        
        self.btn_indir.setEnabled(False)
        self.bar.setValue(0)
        
        self.motor = YtMotor(u, is_mp3, k, kalite)
        self.motor.ilerleme.connect(lambda y, t, h: (self.bar.setValue(y), self.lbl_durum.setText(t), self.lbl_hiz.setText(h)))
        self.motor.finished.connect(lambda: self.btn_indir.setEnabled(True))
        self.motor.start()