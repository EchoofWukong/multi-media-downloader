import os
import time
import json
import glob
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
                             QLabel, QTreeWidget, QTreeWidgetItem, QComboBox, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

os.environ['WDM_LOG'] = '0' 
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.microsoft import EdgeChromiumDriverManager

import core  

# --- 1. TAKİPÇİ ÇEKME MOTORU ---
class TakipciCekmeMotoru(QThread):
    anlik_veri_sinyali = pyqtSignal(dict)
    bilgi_sinyali = pyqtSignal(str)
    islem_bitti_sinyali = pyqtSignal()
    
    def __init__(self, hedef):
        super().__init__()
        # URL girilirse temizleyip sadece kullanıcı adını bırak
        hedef = hedef.replace("https://www.instagram.com/", "").replace("http://www.instagram.com/", "").strip("/")
        self.hedef = hedef.split("?")[0]
        
    def run(self):
        toplanan = {}
        profil_yolu = os.path.join(os.getcwd(), "BotKlasoru")
        options = webdriver.EdgeOptions()
        options.add_argument(f"user-data-dir={profil_yolu}")
        
        # Tarayıcıyı tam ekran ve görünür (headless olmadan) başlatıyoruz
        options.add_argument("--start-maximized") 
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        
        self.bilgi_sinyali.emit("Tarayıcı ekranda açılıyor...")
        
        try:
            driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
            
            self.bilgi_sinyali.emit(f"@{self.hedef} profiline gidiliyor...")
            driver.get(f"https://www.instagram.com/{self.hedef}/")
            time.sleep(5)
            
            self.bilgi_sinyali.emit("Klavye ile Takipçiler menüsü açılıyor...")
            
            # Klavye ile 14 kez TAB basarak "Takipçiler" linkini tetikle
            klavye = ActionChains(driver)
            for _ in range(14): 
                klavye.send_keys(Keys.TAB)
            klavye.perform()
            time.sleep(0.5)
            ActionChains(driver).send_keys(Keys.ENTER).perform()
            time.sleep(3) 
            
            kutu = driver.find_element(By.XPATH, "//div[@role='dialog']//div[contains(@class, '_aano') or contains(@class, 'xyi19xy') or contains(@class, 'x1n2onr6')]")
            
            son_sayi, deneme = 0, 0
            js_kodu = """
            let ext = {};
            document.querySelectorAll("div[role='dialog'] a").forEach(a => {
                let h = a.getAttribute("href");
                if (h && h.startsWith('/') && h.length > 2) {
                    let u = h.split('/')[1];
                    if (u && !['explore', 'reels', 'direct', 'p'].includes(u)) {
                        let p = a.parentElement, c = 0;
                        while (p && p.innerText && !p.innerText.includes('\\n') && c < 6) { p = p.parentElement; c++; }
                        if (p && p.innerText) ext[u] = p.innerText;
                    }
                }
            });
            let links = document.querySelectorAll("div[role='dialog'] a");
            if(links.length > 0) links[links.length - 1].scrollIntoView(true);
            return ext;
            """
            
            self.bilgi_sinyali.emit("Tarama başlatıldı...")
            
            while True:
                sonuclar = driver.execute_script(js_kodu, kutu)
                for uname, text in sonuclar.items():
                    if uname not in toplanan:
                        satirlar = text.split('\n')
                        isim = satirlar[1] if len(satirlar)>=2 and satirlar[1] not in ["Takip Et", "Takip ediliyor"] else ""
                        veri = {"username": uname, "full_name": isim}
                        toplanan[uname] = veri
                        self.anlik_veri_sinyali.emit(veri)
                
                guncel = len(toplanan)
                if guncel == son_sayi:
                    deneme += 1
                    if deneme >= 4: break 
                    self.bilgi_sinyali.emit(f"Takipçiler yükleniyor... ({deneme}/4)")
                    time.sleep(1.5)
                else:
                    deneme, son_sayi = 0, guncel
                    self.bilgi_sinyali.emit(f"Anlık Havuz: {guncel} kişi çekildi")
                    time.sleep(0.7)
                    
            # Taramayı bitirip sonucu yerel diske JSON olarak kaydet
            dosya_adi = f"{self.hedef}.json"
            with open(dosya_adi, "w", encoding="utf-8") as f:
                json.dump({"users": list(toplanan.values())}, f, ensure_ascii=False, indent=4)
            
            self.bilgi_sinyali.emit(f"Tarama bitti ve {dosya_adi} dosyasına kaydedildi! Toplam: {len(toplanan)} kişi.")
            
        except Exception as e:
            self.bilgi_sinyali.emit(f"Hata: {str(e)[:50]}")
        finally:
            self.islem_bitti_sinyali.emit()
            try: driver.quit()
            except: pass

# --- 2. ARAYÜZ (SEKME) ---
class InstagramToplayiciSayfasi(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        
        ust_layout = QHBoxLayout()
        baslik = QLabel("👥 Instagram Takipçi Toplayıcı")
        baslik.setProperty("class", "baslik")
        
        self.btn_kurulum = QPushButton("⚙️ Hesap Girişi Yap / Değiştir")
        self.btn_kurulum.setProperty("class", "normal")
        self.btn_kurulum.setFixedSize(220, 40)
        self.btn_kurulum.clicked.connect(self.hesap_kurulum_baslat)
        
        ust_layout.addWidget(baslik)
        ust_layout.addStretch()
        ust_layout.addWidget(self.btn_kurulum)
        layout.addLayout(ust_layout)
        
        self.lbl_kurulum_durum = QLabel("Durum: Giriş bekleniyor. Eğer hesap eklendiyse direkt tarama yapabilirsiniz.")
        self.lbl_kurulum_durum.setProperty("class", "alt_metin")
        self.lbl_kurulum_durum.setStyleSheet("color: #a6e3a1; margin-bottom: 10px;")
        layout.addWidget(self.lbl_kurulum_durum)
        
        tarama_layout = QHBoxLayout()
        self.hedef_input = QLineEdit()
        self.hedef_input.setPlaceholderText("Takipçileri çekilecek Kullanıcı Adı veya Link (Örn: natgeo)")
        self.hedef_input.setFixedHeight(45)
        
        self.btn_tara = QPushButton("⚡ Takipçileri Çek")
        self.btn_tara.setProperty("class", "indir_btn")
        self.btn_tara.setFixedSize(180, 45)
        self.btn_tara.clicked.connect(self.tarama_baslat)
        
        tarama_layout.addWidget(self.hedef_input)
        tarama_layout.addWidget(self.btn_tara)
        layout.addLayout(tarama_layout)
        
        filtre_layout = QHBoxLayout()
        filtre_lbl = QLabel("Filtrele:")
        self.cinsiyet_filtresi = QComboBox()
        self.cinsiyet_filtresi.addItems(["Tümü", "Kadın", "Erkek", "Belirsiz"])
        self.cinsiyet_filtresi.setFixedWidth(200)
        self.cinsiyet_filtresi.currentTextChanged.connect(self.agaci_filtrele)
        
        self.lbl_istatistik = QLabel("Toplam: 0")
        self.lbl_istatistik.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        filtre_layout.addWidget(filtre_lbl)
        filtre_layout.addWidget(self.cinsiyet_filtresi)
        filtre_layout.addStretch()
        filtre_layout.addWidget(self.lbl_istatistik)
        layout.addLayout(filtre_layout)
        
        self.agac = QTreeWidget()
        self.agac.setHeaderLabels(["No", "Hesap / Kullanıcı Adı", "Tam İsim", "Cinsiyet Tahmini"])
        self.agac.setStyleSheet("""
            QTreeWidget { background-color: #151b2d; color: #ffffff; border: 1px solid #2a3050; border-radius: 6px; outline: none; }
            QTreeWidget::item { padding: 6px; border-bottom: 1px solid #1e1e2e; }
            QTreeWidget::item:selected { background-color: #313244; }
            QHeaderView::section { background-color: #0f1424; color: #8a93ad; padding: 10px; font-weight: bold; border: none; }
        """)
        self.agac.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.agac.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.agac.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.agac.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.agac.setAlternatingRowColors(False)
        
        layout.addWidget(self.agac)
        
        self.cekme_motoru = None
        self.aktif_kok = None
        self.aktif_hedef = ""
        self.toplam_cekilen = 0
        
        # Açılışta klasördeki JSON arşiv dosyalarını yükle
        self.arsivleri_yukle()

    def arsivleri_yukle(self):
        for dosya in glob.glob("*.json"):
            if dosya in ["isim_veritabani.json", "favoriler.json", "veri.json"]:
                continue
                
            hedef_adi = dosya.replace(".json", "")
            
            try:
                with open(dosya, "r", encoding="utf-8") as f:
                    veri = json.load(f)
                    kullanicilar = veri.get("users", [])
                    
                    if not kullanicilar:
                        continue
                        
                    kok = QTreeWidgetItem(self.agac)
                    kok.setText(1, f"📁 {hedef_adi} (Toplam: {len(kullanicilar)} Takipçi)")
                    kok.setForeground(1, QColor("#cba6f7"))
                    kok.setExpanded(False) 
                    
                    for idx, k in enumerate(kullanicilar):
                        uname = k.get("username", "")
                        fname = k.get("full_name", "")
                        cinsiyet, skor = core.cinsiyet_analizi(uname, fname)
                        
                        cocuk = QTreeWidgetItem(kok)
                        cocuk.setText(0, str(idx + 1))
                        cocuk.setText(1, uname)
                        cocuk.setText(2, fname)
                        cocuk.setText(3, cinsiyet)
                        cocuk.setTextAlignment(0, Qt.AlignCenter)
                        cocuk.setTextAlignment(3, Qt.AlignCenter)
                        
                        if cinsiyet == "Kadın":
                            cocuk.setForeground(3, QColor("#f5c2e7"))
                        elif cinsiyet == "Erkek":
                            cocuk.setForeground(3, QColor("#89b4fa"))
                        else:
                            cocuk.setForeground(3, QColor("#a6adc8"))
                            
                        self.toplam_cekilen += 1
                        
            except Exception as e:
                print(f"{dosya} yüklenirken hata oluştu: {e}")
                
        self.lbl_istatistik.setText(f"Toplam Taranan Kişi (Arşiv): {self.toplam_cekilen}")

    def hesap_kurulum_baslat(self):
        msg = QMessageBox()
        msg.setWindowTitle("Hesap Girişi")
        msg.setText("Tamam'a bastığınızda yeni bir siyah terminal penceresi açılacak. Oradan tarayıcı açılıp hesabınıza giriş yapın ve 'Bilgilerimi Kaydet' deyin. Terminalde ENTER'a basıp bitirdikten sonra buradan tarama yapabilirsiniz.")
        msg.exec_()
        
        self.lbl_kurulum_durum.setText("Durum: İlk kurulum ekranı (Terminal) açıldı...")
        subprocess.Popen("start cmd /k python ilk_kurulum.py", shell=True)

    def tarama_baslat(self):
        hedef_ham = self.hedef_input.text().strip()
        if not hedef_ham:
            self.lbl_kurulum_durum.setText("Lütfen bir kullanıcı adı veya link girin!")
            return
            
        self.aktif_hedef = hedef_ham.replace("https://www.instagram.com/", "").replace("http://www.instagram.com/", "").strip("/").split("?")[0]
        
        self.btn_tara.setEnabled(False)
        self.btn_kurulum.setEnabled(False)
        
        self.aktif_kok = QTreeWidgetItem(self.agac)
        self.aktif_kok.setText(1, f"📁 {self.aktif_hedef} (Taranıyor...)")
        self.aktif_kok.setForeground(1, QColor("#a6e3a1"))
        self.aktif_kok.setExpanded(True)
        
        self.cekme_motoru = TakipciCekmeMotoru(self.aktif_hedef)
        self.cekme_motoru.bilgi_sinyali.connect(lambda m: self.lbl_kurulum_durum.setText(f"Durum: {m}"))
        self.cekme_motoru.anlik_veri_sinyali.connect(self.agaca_ekle)
        self.cekme_motoru.islem_bitti_sinyali.connect(self.tarama_bitti)
        self.cekme_motoru.start()

    def agaca_ekle(self, veri):
        uname = veri["username"]
        fname = veri["full_name"]
        cinsiyet, skor = core.cinsiyet_analizi(uname, fname)
        
        cocuk = QTreeWidgetItem(self.aktif_kok)
        cocuk.setText(0, str(self.aktif_kok.childCount()))
        cocuk.setText(1, uname)
        cocuk.setText(2, fname)
        cocuk.setText(3, cinsiyet)
        cocuk.setTextAlignment(0, Qt.AlignCenter)
        cocuk.setTextAlignment(3, Qt.AlignCenter)
        
        if cinsiyet == "Kadın":
            cocuk.setForeground(3, QColor("#f5c2e7"))
        elif cinsiyet == "Erkek":
            cocuk.setForeground(3, QColor("#89b4fa"))
        else:
            cocuk.setForeground(3, QColor("#a6adc8"))
            
        self.toplam_cekilen += 1
        
        secili_cins = self.cinsiyet_filtresi.currentText()
        if secili_cins != "Tümü" and secili_cins != cinsiyet:
            cocuk.setHidden(True)
            
        self.lbl_istatistik.setText(f"Toplam Taranan Kişi: {self.toplam_cekilen}")

    def agaci_filtrele(self):
        secili = self.cinsiyet_filtresi.currentText()
        gosterilen = 0
        
        for i in range(self.agac.topLevelItemCount()):
            kok = self.agac.topLevelItem(i)
            kok_gizli = True
            
            for j in range(kok.childCount()):
                cocuk = kok.child(j)
                cinsiyet = cocuk.text(3)
                
                if secili == "Tümü" or cinsiyet == secili:
                    cocuk.setHidden(False)
                    kok_gizli = False
                    gosterilen += 1
                else:
                    cocuk.setHidden(True)
                    
            kok.setHidden(kok_gizli)
            
        self.lbl_istatistik.setText(f"Gösterilen: {gosterilen} / Toplam Çekilen: {self.toplam_cekilen}")

    def tarama_bitti(self):
        if self.aktif_kok:
            kisi_sayisi = self.aktif_kok.childCount()
            self.aktif_kok.setText(1, f"📁 {self.aktif_hedef} (Toplam: {kisi_sayisi} Takipçi)")
            self.aktif_kok.setForeground(1, QColor("#cba6f7"))
            
        self.btn_tara.setEnabled(True)
        self.btn_kurulum.setEnabled(True)