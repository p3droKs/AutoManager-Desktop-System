import sys
from PySide6.QtWidgets import QApplication
from db import init_db
from views.login_window import LoginWindow

def main():
    init_db()
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
