from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget
from tiktok import TikTokSayfasi
from instagram import InstagramSayfasi
from youtube import YouTubeSayfasi
from instagram_toplayici import InstagramToplayiciSayfasi

class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi Downloader")
        self.resize(950, 750)
        self.setMinimumSize(800, 600)
        
        # Orijinal Birebir Stillerin Geri Getirildi
        self.setStyleSheet("""
            QMainWindow { background-color: #0a0d18; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #ffffff; }
            
            /* Sol Menü */
            QListWidget { background-color: #151b2d; color: #8a93ad; border: none; border-right: 2px solid #0a0d18; padding: 15px; outline: none; }
            QListWidget::item { padding: 15px; border-radius: 8px; font-size: 15px; font-weight: bold; margin-bottom: 5px; }
            QListWidget::item:hover { background-color: #1b2a5e; color: #cdd6f4; }
            QListWidget::item:selected { background-color: #1b2a5e; color: #6b8aff; border-left: 4px solid #6b8aff; }
            
            /* Sağ Taraf Ortak Stiller */
            QLabel.baslik { font-size: 24px; font-weight: bold; margin-bottom: 5px; }
            QLabel.alt_metin { color: #8a93ad; font-size: 13px; }
            QLineEdit { background-color: #0f1424; border: 2px solid #2a3050; border-radius: 10px; padding: 10px; font-size: 14px; }
            QLineEdit:focus { border: 2px solid #6b8aff; }
            
            QPushButton.normal { background-color: #0f1424; border: 2px solid #2a3050; border-radius: 10px; color: #6b8aff; font-weight: bold; }
            QPushButton.normal:hover { background-color: #1b2a5e; }
            
            QPushButton.kart { background-color: #0f1424; border: 2px solid #2a3050; border-radius: 10px; font-size: 14px; font-weight: bold; }
            QPushButton.kart:hover { background-color: #1b2a5e; }
            QPushButton.kart:checked { background-color: #1b2a5e; border: 2px solid #6b8aff; color: #ffffff; }
            
            QPushButton.indir_btn { background-color: #6b8aff; color: #0a0d18; font-size: 20px; font-weight: bold; border-radius: 14px; }
            QPushButton.indir_btn:hover { background-color: #5574e6; }
            QPushButton.indir_btn:disabled { background-color: #2a3050; color: #8a93ad; }
            
            QProgressBar { border: none; border-radius: 4px; background-color: #252c4a; color: transparent; }
            QProgressBar::chunk { background-color: #6b8aff; border-radius: 4px; }
            
            /* IG Toplayıcı Tablosu ve Dropdown İçin Eklenen Stiller */
            QTableWidget { background-color: #151b2d; color: #ffffff; border: 1px solid #2a3050; border-radius: 6px; gridline-color: #2a3050; }
            QHeaderView::section { background-color: #0f1424; color: #8a93ad; padding: 8px; font-weight: bold; border: none; }
            QComboBox { background-color: #0f1424; border: 2px solid #2a3050; border-radius: 10px; padding: 10px; color: #ffffff; font-size: 14px; font-weight: bold; }
            QComboBox QAbstractItemView { 
                background-color: #151b2d; 
                color: #ffffff; 
                selection-background-color: #1b2a5e;
                selection-color: #6b8aff;
                border: 1px solid #2a3050;
                outline: none;
            }
        """)
        
        merkez = QWidget()
        self.setCentralWidget(merkez)
        layout = QHBoxLayout(merkez)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.sol_menu = QListWidget()
        self.sol_menu.addItems(["📸 Instagram Medya", "▶️ YouTube", "🎵 TikTok", "👥 IG Toplayıcı"])
        self.sol_menu.setFixedWidth(220)
        
        self.sayfalar = QStackedWidget()
        self.sayfalar.addWidget(InstagramSayfasi())
        self.sayfalar.addWidget(YouTubeSayfasi())
        self.sayfalar.addWidget(TikTokSayfasi()) 
        self.sayfalar.addWidget(InstagramToplayiciSayfasi()) 
        
        layout.addWidget(self.sol_menu)
        layout.addWidget(self.sayfalar)
        
        self.sol_menu.currentRowChanged.connect(self.sayfalar.setCurrentIndex)
        self.sol_menu.setCurrentRow(0)