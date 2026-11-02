import os
import sys

# Hayati Ayar: Tarayıcı motorunun ekrana yazı yazmaya çalışıp EXE'yi çökertmesini engeller
os.environ['WDM_LOG'] = '0' 

try:
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from webdriver_manager.microsoft import EdgeChromiumDriverManager

    print("="*40)
    print(" PROANALİZ - İLK KURULUM VE GİRİŞ ")
    print("="*40)
    print("\n[!] Açılan tarayıcıda Instagram hesabınıza giriş yapın.")
    print("[!] Giriş yaptıktan sonra 'Bilgilerini Kaydet' butonuna basmayı unutmayın!")
    print("[!] Bu işlem sayesinde ana program bir daha şifre sormayacaktır.\n")

    profil_yolu = os.path.join(os.getcwd(), "BotKlasoru")
    options = webdriver.EdgeOptions()
    options.add_argument(f"user-data-dir={profil_yolu}")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    driver.get("https://www.instagram.com/accounts/login/")
    
    input("Giriş başarılıysa programı kapatmak için ENTER'a basın...")
    driver.quit()
    print("Kurulum tamamlandı! Artık 'ProAnaliz' uygulamasını başlatabilirsiniz.")

except Exception as e:
    print("\n[HATA OLUŞTU!]")
    print(f"Detay: {e}")
    input("\nÇıkmak için ENTER'a basın...")