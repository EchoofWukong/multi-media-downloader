import time
import os
import json
import re
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.microsoft import EdgeChromiumDriverManager

class ProfilResmiIndirici(QThread):
    resim_hazir = pyqtSignal(str, bytes)
    def __init__(self, username):
        super().__init__()
        self.kullanici_adi = username
        
    def run(self):
        try:
            url = f"https://www.instagram.com/{self.kullanici_adi}/"
            headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
            cevap = requests.get(url, headers=headers, timeout=4)
            
            match = re.search(r'<meta property="og:image" content="([^"]+)"', cevap.text)
            if match:
                resim_url = match.group(1).replace("&amp;", "&")
                # HD Kalite Hilesi: Instagram'ın kalite düşürücü (s150x150 vb.) eklerini URL'den siler!
                resim_url = re.sub(r's\d+x\d+/', '', resim_url)
                
                resim_cevap = requests.get(resim_url, timeout=5)
                if resim_cevap.status_code == 200:
                    self.resim_hazir.emit(self.kullanici_adi, resim_cevap.content)
                    return
                    
            yedek_url = f"https://ui-avatars.com/api/?name={self.kullanici_adi}&background=cba6f7&color=11111b&size=256"
            self.resim_hazir.emit(self.kullanici_adi, requests.get(yedek_url).content)
        except: self.resim_hazir.emit(self.kullanici_adi, b"")

class VeriCekmeMotoru(QThread):
    anlik_veri_sinyali = pyqtSignal(dict)
    bilgi_sinyali = pyqtSignal(str)
    islem_bitti_sinyali = pyqtSignal(str)
    def __init__(self, hedef):
        super().__init__()
        self.hedef = hedef
        
    def run(self):
        dosya = f"{self.hedef}.json"
        toplanan = {}
        if os.path.exists(dosya):
            try:
                with open(dosya, "r", encoding="utf-8") as f:
                    for k in json.load(f).get("users", []): toplanan[k["username"]] = k
            except: pass

        options = webdriver.EdgeOptions()
        options.add_argument(f"user-data-dir={os.path.join(os.getcwd(), 'BotKlasoru')}")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)
        
        self.bilgi_sinyali.emit("Tarayıcı başlatılıyor...")
        driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
        
        try:
            driver.get(f"https://www.instagram.com/{self.hedef}/")
            time.sleep(5)
            klavye = ActionChains(driver)
            for _ in range(14): klavye.send_keys(Keys.TAB)
            klavye.perform()
            time.sleep(0.5)
            ActionChains(driver).send_keys(Keys.ENTER).perform()
            time.sleep(3) 
            
            kutu = driver.find_element(By.XPATH, "//div[@role='dialog']//div[contains(@class, '_aano') or contains(@class, 'xyi19xy') or contains(@class, 'x1n2onr6')]")
            son_sayi, deneme = len(toplanan), 0
            
            js = """
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
            
            while True:
                for uname, text in driver.execute_script(js, kutu).items():
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
                    self.bilgi_sinyali.emit(f"Bekleniyor... ({deneme}/4)")
                    time.sleep(1.5)
                else:
                    deneme, son_sayi = 0, guncel
                    self.bilgi_sinyali.emit(f"Anlık Havuz: {guncel} kişi")
                    time.sleep(0.7) 

            with open(dosya, "w", encoding="utf-8") as f:
                json.dump({"users": list(toplanan.values())}, f, ensure_ascii=False, indent=4)
            self.islem_bitti_sinyali.emit(dosya)
        except Exception as e: self.bilgi_sinyali.emit(f"Hata: {str(e)}")
        finally: driver.quit()