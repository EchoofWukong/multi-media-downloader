from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class FacebookSayfasi(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        baslik = QLabel("Facebook Araçları")
        baslik.setObjectName("sayfa_baslik")
        
        bilgi = QLabel("Facebook sayfası çok yakında kodlanacak...")
        bilgi.setObjectName("sayfa_alt_baslik")
        
        layout.addWidget(baslik)
        layout.addWidget(bilgi)
        layout.addStretch()