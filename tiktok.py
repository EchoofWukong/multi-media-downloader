import os, requests
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
                             QLabel, QProgressBar, QFileDialog, QButtonGroup, QApplication, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

def son_klasoru_al():
    if os.path.exists("son_klasor.txt"):
        with open("son_klasor.txt", "r", encoding="utf-8") as f:
            klasor = f.read().strip()
            if os.path.exists(klasor): return klasor
    return os.path.join(os.path.expanduser("~"), "Desktop")

def son_klasoru_kaydet(klasor):
    with open("son_klasor.txt", "w", encoding="utf-8") as f:
        f.write(klasor)

# --- YENİ NESİL TIKTOK MOTORU (Yt-Dlp olmadan, Filigransız) ---
class TtMotor(QThread):
    ilerleme = pyqtSignal(int, str, str)
    
    def __init__(self, url, mod, klasor):
        super().__init__()
        self.url = url.split('?')[0] # Temiz link
        self.mod = mod
        self.klasor = klasor

    def run(self):
        try:
            self.ilerleme.emit(10, "TikTok sunucusuna bağlanılıyor...", "")
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            api_url = f"https://www.tikwm.com/api/?url={self.url}"
            
            r = requests.get(api_url, headers=headers, timeout=15)
            data = r.json()
            
            if data.get("code") != 0:
                raise RuntimeError("Link hatalı veya video gizli.")
                
            v_data = data.get("data", {})
            author = v_data.get("author", {}).get("unique_id", "tiktok")
            v_id = v_data.get("id", "video")
            
            if self.mod == "photo":
                avatar = v_data.get("author", {}).get("avatar")
                self.dosya_indir(avatar, f"{author}_profil.jpg")
            elif self.mod == "audio":
                music = v_data.get("music")
                self.dosya_indir(music, f"{author}_{v_id} (Ses).mp3")
            else:
                play = v_data.get("play") # Filigransız video adresi
                self.dosya_indir(play, f"{author}_{v_id} (TikTok).mp4")
                
        except Exception as e:
            self.ilerleme.emit(0, f"Hata: {str(e)[:70]}", "")

    def dosya_indir(self, link, dosya_adi):
        if not link:
            raise RuntimeError("Medya bulunamadı.")
            
        self.ilerleme.emit(30, "İndirme başlıyor...", "")
        tam_yol = os.path.join(self.klasor, dosya_adi)
        
        r = requests.get(link, stream=True, timeout=15)
        total = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(tam_yol, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*64):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        yuzde = int((downloaded / total) * 100)
                        self.ilerleme.emit(yuzde, f"İndiriliyor... %{yuzde}", "")
                    else:
                        self.ilerleme.emit(50, f"İndiriliyor... ({downloaded // 1024} KB)", "")
                        
        self.ilerleme.emit(100, "Bitti ✔", "")


# --- TIKTOK ARAYÜZÜ ---
class TikTokSayfasi(QWidget):
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
        
        baslik = QLabel("TikTok İndirme Araçları")
        baslik.setProperty("class", "baslik")
        layout.addWidget(baslik)
        
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("TikTok Linki veya Kullanıcı Adı Girin...")
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
        self.btn_video = QPushButton("Video (Yazısız)\nmp4")
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
        if not u: return self.lbl_durum.setText("Lütfen link girin!")
        m = "audio" if self.btn_ses.isChecked() else "photo" if self.btn_profil.isChecked() else "video"
        
        self.btn_indir.setEnabled(False)
        self.bar.setValue(0)
        self.motor = TtMotor(u, m, k)
        self.motor.ilerleme.connect(lambda y, t, h: (self.bar.setValue(y), self.lbl_durum.setText(t), self.lbl_hiz.setText(h)))
        self.motor.finished.connect(lambda: self.btn_indir.setEnabled(True))
        self.motor.start()