import sys
from PyQt5.QtWidgets import QApplication
from gui import AnaPencere

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = AnaPencere()
    pencere.show()
    sys.exit(app.exec_())