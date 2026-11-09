import os
import json
import requests
import subprocess
from urllib.parse import urlparse, unquote
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QProgressBar, QFileDialog, 
                             QMessageBox, QCheckBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

GECMIS_DOSYASI = "genel_indirici_gecmis.json"

class IndirmeThread(QThread):
    progress_guncelle = pyqtSignal(int)
    durum_guncelle = pyqtSignal(str)
    tamamlandi = pyqtSignal(str) 

    def __init__(self, url, kayit_yolu):
        super().__init__()
        self.url = url
        self.kayit_yolu = kayit_yolu

    def run(self):
        try:
            self.durum_guncelle.emit("Bağlantı kuruluyor...")
            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()

            toplam_boyut = int(response.headers.get('content-length', 0))
            if toplam_boyut == 0:
                self.durum_guncelle.emit("Dosya boyutu bilinemiyor, indiriliyor...")

            indirilen = 0
            chunk_size = 1024 * 1024  

            with open(self.kayit_yolu, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        indirilen += len(chunk)
                        if toplam_boyut > 0:
                            yuzde = int((indirilen / toplam_boyut) * 100)
                            self.progress_guncelle.emit(yuzde)

            self.durum_guncelle.emit("✅ İndirme Tamamlandı!")
            self.progress_guncelle.emit(100)
            self.tamamlandi.emit(self.kayit_yolu)
            
        except requests.exceptions.MissingSchema:
            self.durum_guncelle.emit("❌ Hata: Link 'http://' veya 'https://' ile başlamalıdır.")
            self.tamamlandi.emit("") 
        except Exception as e:
            self.durum_guncelle.emit(f"❌ İndirme hatası: {str(e)}")
            self.progress_guncelle.emit(0)
            self.tamamlandi.emit("")
            
class GenelIndiriciSayfasi(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        baslik = QLabel("Genel Dosya İndirici")
        baslik.setProperty("class", "baslik")
        
        alt_metin = QLabel("Oyun, program veya herhangi bir dosyanın doğrudan indirme linkini yapıştırın.")
        alt_metin.setProperty("class", "alt_metin")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("İndirme linkini buraya yapıştırın (http:// veya https://)...")

        # --- DÜZELTİLMİŞ CHECKBOX'LAR ---
        cb_layout = QHBoxLayout()
        # indicator kısmındaki CSS hatası düzeltildi, artık tıklanabilir
        cb_style = "QCheckBox { color: #cdd6f4; font-size: 13px; font-weight: bold; padding: 5px; }"
        
        self.oto_ac_cb = QCheckBox("İndirme Bittiğinde Otomatik Aç")
        self.oto_ac_cb.setStyleSheet(cb_style)
        self.oto_ac_cb.setChecked(True)

        self.guvenlik_cb = QCheckBox("Tehlikeli Dosyaları (.exe, .bat) Çalıştır")
        self.guvenlik_cb.setStyleSheet(cb_style)
        self.guvenlik_cb.setChecked(False)

        cb_layout.addWidget(self.oto_ac_cb)
        cb_layout.addWidget(self.guvenlik_cb)
        cb_layout.addStretch()

        self.indir_btn = QPushButton("İNDİR")
        self.indir_btn.setProperty("class", "indir_btn")
        self.indir_btn.setFixedHeight(50)
        self.indir_btn.clicked.connect(self.indirme_baslat)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(25)

        self.durum_label = QLabel("Hazır")
        self.durum_label.setProperty("class", "alt_metin")
        self.durum_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        gecmis_baslik = QLabel("İndirme Geçmişi (Klasörde görmek için çift tıklayın)")
        gecmis_baslik.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px; color: #8a93ad;")
        
        self.gecmis_listesi = QListWidget()
        self.gecmis_listesi.setStyleSheet("""
            QListWidget {
                background-color: #0f1424; border: 2px solid #2a3050; border-radius: 10px;
                padding: 5px; color: #8a93ad; font-size: 13px;
            }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #1b2a5e; }
            QListWidget::item:hover { background-color: #1b2a5e; color: #ffffff; border-radius: 5px; }
        """)
        self.gecmis_listesi.itemDoubleClicked.connect(self.gecmis_cift_tiklandi)

        layout.addWidget(baslik)
        layout.addWidget(alt_metin)
        layout.addWidget(self.url_input)
        layout.addLayout(cb_layout)
        layout.addWidget(self.indir_btn)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.durum_label)
        layout.addWidget(gecmis_baslik)
        layout.addWidget(self.gecmis_listesi)

        # Uygulama açıldığında geçmişi yükle
        self.gecmisi_yukle()

    # --- GEÇMİŞ YÜKLEME VE KAYDETME SİSTEMİ ---
    def gecmisi_yukle(self):
        if os.path.exists(GECMIS_DOSYASI):
            try:
                with open(GECMIS_DOSYASI, 'r', encoding='utf-8') as f:
                    gecmis_verileri = json.load(f)
                    for veri in gecmis_verileri:
                        self.gecmis_ui_ekle(veri['dosya_adi'], veri['kayit_yolu'], uste_ekle=False)
            except Exception:
                pass

    def gecmisi_kaydet(self, dosya_adi, kayit_yolu):
        gecmis_verileri = []
        if os.path.exists(GECMIS_DOSYASI):
            try:
                with open(GECMIS_DOSYASI, 'r', encoding='utf-8') as f:
                    gecmis_verileri = json.load(f)
            except Exception:
                pass
        
        # Yeni indirmeyi en başa ekle
        gecmis_verileri.insert(0, {"dosya_adi": dosya_adi, "kayit_yolu": kayit_yolu})
        
        try:
            with open(GECMIS_DOSYASI, 'w', encoding='utf-8') as f:
                json.dump(gecmis_verileri, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def gecmis_ui_ekle(self, dosya_adi, kayit_yolu, uste_ekle=True):
        gecmis_metni = f"📁 {dosya_adi}"
        item = QListWidgetItem(gecmis_metni)
        item.setData(Qt.UserRole, kayit_yolu)
        
        if uste_ekle:
            self.gecmis_listesi.insertItem(0, item)
        else:
            self.gecmis_listesi.addItem(item)
    # ------------------------------------------

    def indirme_baslat(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Hata", "Lütfen bir link girin!")
            return

        dosya_adi = "indirilen_dosya"
        
        try:
            parsed_url = urlparse(url)
            path_filename = os.path.basename(parsed_url.path)
            
            if path_filename and '.' in path_filename:
                dosya_adi = unquote(path_filename)
            else:
                query_string = parsed_url.query
                params = dict(qc.split("=") for qc in query_string.split("&") if "=" in qc)
                
                if 'name' in params:
                    dosya_adi = unquote(params['name'])
                    if '.' not in dosya_adi and path_filename and '.' in path_filename:
                       dosya_adi += os.path.splitext(path_filename)[1]
                elif 'filename' in params:
                    dosya_adi = unquote(params['filename'])
        except Exception:
            pass
        
        if '.' not in dosya_adi and '.mp3' in url.lower(): dosya_adi += '.mp3'
        elif '.' not in dosya_adi and '.mp4' in url.lower(): dosya_adi += '.mp4'
        elif '.' not in dosya_adi and '.zip' in url.lower(): dosya_adi += '.zip'
        elif '.' not in dosya_adi and '.rar' in url.lower(): dosya_adi += '.rar'
        elif '.' not in dosya_adi and '.exe' in url.lower(): dosya_adi += '.exe'

        kaydetme_yolu, _ = QFileDialog.getSaveFileName(
            self, "Dosyayı Nereye Kaydetmek İstersiniz?", dosya_adi, "Tüm Dosyalar (*.*)"
        )

        if not kaydetme_yolu:
            self.durum_label.setText("İndirme iptal edildi.")
            return

        self.indir_btn.setEnabled(False)
        self.indir_btn.setText("⏳ İNDİRİLİYOR...")
        self.progress_bar.setValue(0)
        self.durum_label.setText("Bağlanıyor ve indiriliyor...")
        
        self.thread = IndirmeThread(url, kaydetme_yolu)
        self.thread.progress_guncelle.connect(self.progress_bar.setValue)
        self.thread.durum_guncelle.connect(self.durum_label.setText)
        self.thread.tamamlandi.connect(self.indirme_bitti)
        self.thread.start()

    def indirme_bitti(self, kayit_yolu):
        self.indir_btn.setEnabled(True)
        self.indir_btn.setText("İNDİR")
        self.progress_bar.setValue(0) # %100 BARINI SIFIRLAR
        
        if kayit_yolu: 
            self.url_input.clear()
            dosya_adi = os.path.basename(kayit_yolu)
            
            # Arayüze ve JSON dosyasına kaydet
            self.gecmis_ui_ekle(dosya_adi, kayit_yolu, uste_ekle=True)
            self.gecmisi_kaydet(dosya_adi, kayit_yolu)
            
            if self.oto_ac_cb.isChecked():
                tehlikeli_uzantilar = ['.exe', '.bat', '.cmd', '.vbs', '.ps1', '.msi']
                _, ext = os.path.splitext(kayit_yolu)
                
                try:
                    if ext.lower() in tehlikeli_uzantilar and not self.guvenlik_cb.isChecked():
                        subprocess.run(['explorer', '/select,', os.path.normpath(kayit_yolu)])
                    else:
                        os.startfile(kayit_yolu)
                except Exception as e:
                    QMessageBox.warning(self, "Hata", f"Dosya açılamadı: {e}")

    def gecmis_cift_tiklandi(self, item):
        dosya_yolu = item.data(Qt.UserRole)
        
        if dosya_yolu and os.path.exists(dosya_yolu):
            try:
                subprocess.run(['explorer', '/select,', os.path.normpath(dosya_yolu)])
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Klasör açılamadı: {e}")
        else:
            QMessageBox.warning(self, "Hata", "Dosya bulunamadı! Silinmiş veya yeri değiştirilmiş olabilir.")