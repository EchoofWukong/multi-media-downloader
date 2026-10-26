# 🚀 Multi Media Downloader (PyQt5)

Python ve PyQt5 ile geliştirilmiş, modern ve kullanıcı dostu arayüze sahip profesyonel bir sosyal medya indirme aracıdır. YouTube, Instagram, TikTok ve Facebook platformlarından yüksek hızda ve filigransız medya indirmenizi sağlar.

## 🌟 Özellikler

- **▶️ YouTube:** İstediğiniz çözünürlükte (1080p, 720p vb.) video veya doğrudan MP3 ses indirme.
- **📸 Instagram:** Reels, Video, Fotoğraf ve Profil Fotoğrafı indirme desteği (Gereksiz parametreleri otomatik temizler).
- **🎵 TikTok:** Filigransız (yazısız) video ve orijinal ses (MP3) indirme. Özel API kullanılarak bot korumalarına takılmaz.
- **🟦 Facebook:** Yüksek çözünürlüklü video indirme desteği.
- **🎨 Modern Arayüz:** Göz yormayan koyu tema (Dark Mode), akıcı animasyonlar ve şık UI tasarımı.
- **💾 Akıllı Klasör Hafızası:** Seçtiğiniz son indirme konumunu hatırlar, sizi sürekli klasör seçmekten kurtarır.
- **🛡️ Çökme Koruması:** FFmpeg kurulu olmasa bile program çökmez, otomatik olarak en uygun tek parça formatı bularak indirmeyi tamamlar.

## 🛠️ Kullanılan Teknolojiler
- **Python 3**
- **PyQt5** (Arayüz Tasarımı)
- **yt-dlp** (Ana İndirme Motoru)
- **requests & imageio-ffmpeg** (API haberleşmesi ve medya birleştirme)

## ⚙️ Kurulum ve Kullanım

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

1. Depoyu klonlayın:
```bash
git clone https://github.com/EchoofWukong/multi-media-downloader.git
```

2. Gerekli kütüphaneleri yükleyin:
```bash
pip install PyQt5 yt-dlp requests imageio-ffmpeg
```

3. Uygulamayı başlatın:
```bash
python main.py
```
