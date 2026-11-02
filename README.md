# 🚀 Multi Media Downloader & Analyzer (PyQt5) - v0.2

Python ve PyQt5 ile geliştirilmiş, modern karanlık temaya (Dark Theme) sahip profesyonel bir sosyal medya indirme ve veri analizi aracıdır. YouTube, Instagram ve TikTok platformlarından yüksek hızda medya indirmenizi sağlarken, yeni eklenen analiz motoru ile Instagram profillerini derinlemesine incelemenize olanak tanır.

## 🎉 v0.2 İle Gelen Yeni Özellikler
* **👥 Instagram Takipçi Toplayıcı (Yeni Sekme):** Hedef hesapların takipçi listeleri Selenium ve Edge altyapısı kullanılarak, insan davranışları (klavye simülasyonu) taklit edilip ban riski en aza indirilerek çekilir.
* **🧠 Otomatik Cinsiyet Analizi:** Çekilen takipçilerin isimleri, kısaltmaları ve biyografi emojileri özel bir algoritma (`core.py`) ile analiz edilerek cinsiyet tahminlemesi yapılır.
* **📁 JSON Arşiv Sistemi:** Taranan hesaplar `.json` formatında kaydedilir ve uygulama açıldığında `QTreeWidget` (Ağaç) yapısında filtrelenebilir klasörler halinde listelenir.
* **🕵️ Playwright Entegrasyonu:** Instagram HD Profil Fotoğrafı indirme işlemi, HTML kazımak yerine ağ trafiğini (network interception) dinleyen Playwright motoruna geçirildi.
* **🎨 Gelişmiş Dark Theme:** Tablolar, açılır menüler (`QComboBox`) ve veri listeleri için tam uyumlu karanlık tema düzenlemeleri yapıldı.

## 🌟 Temel Özellikler
* **▶️ YouTube:** İstenilen çözünürlükte (1080p, 720p vb.) video veya `FFmpegExtractAudio` ile doğrudan yüksek kalite MP3 ses indirme.
* **📸 Instagram Medya:** Reels, Video ve Fotoğraf indirme desteği. Gereksiz URL parametrelerini otomatik temizler.
* **🎵 TikTok:** `tikwm` API'si kullanılarak filigransız (yazısız) video ve orijinal ses (MP3) indirme.

## 🛠️ Kurulum Gereksinimleri
Projeyi çalıştırmadan önce sisteminizde Python 3.8+ kurulu olmalıdır. Gerekli kütüphaneleri kurmak için terminalde şu komutu çalıştırın:
```bash
pip install -r requirements.txt
```
Not: Playwright'ın düzgün çalışması için kütüphane kurulumundan sonra playwright install chromium komutunu çalıştırmayı unutmayın.

🚀 Kullanım
Proje dizinindeki main.py dosyasını çalıştırın:

``` bash
python main.py
```
Instagram Toplayıcı İçin İlk Kurulum: "IG Toplayıcı" sekmesindeki Hesap Girişi Yap / Değiştir butonuna tıklayın. Açılan siyah terminal (CMD) penceresi üzerinden Edge tarayıcısı başlayacaktır. Hesabınıza giriş yapıp "Bilgilerimi Kaydet" dedikten sonra sekmeyi kapatın. Sistem BotKlasoru adında yerel bir oturum profili oluşturacaktır.

Çerezler (Cookies): Gizli profillerden veya kısıtlı içeriklerden medya indirmek için, tarayıcınızdan dışa aktardığınız (Netscape formatındaki) güncel çerezleri cookies.txt dosyasının içine yapıştırın.

