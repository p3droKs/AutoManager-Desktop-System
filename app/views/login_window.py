from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox)
from controllers.auth_controller import AuthController
from views.cadastro_window import CadastroWindow
from views.main_window import MainWindow

class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AutoManager - Login")
        self.auth = AuthController()
        self.authenticated_user = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Login"))
        self.input_user = QLineEdit(); self.input_user.setPlaceholderText("Usuário")
        self.input_pass = QLineEdit(); self.input_pass.setPlaceholderText("Senha")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        btn_login = QPushButton("Entrar"); btn_login.clicked.connect(self.on_login)

        btn_cadastro = QPushButton("Cadastrar-se")
        btn_cadastro.clicked.connect(self.on_open_cadastro)

        layout.addWidget(self.input_user)
        layout.addWidget(self.input_pass)
        layout.addWidget(btn_login)
        layout.addWidget(btn_cadastro)

        btn_quit = QPushButton("Fechar")
        btn_quit.clicked.connect(self.close)
        layout.addWidget(btn_quit)

    def on_login(self):
        user = self.input_user.text().strip()
        pwd = self.input_pass.text().strip()
        if not user or not pwd:
            QMessageBox.warning(self, "Erro", "Preencha usuário e senha")
            return
        auth_user = self.auth.authenticate(user, pwd)
        if auth_user:
            QMessageBox.information(self, "Ok", f"Bem-vindo, {auth_user.nome}")
            self.authenticated_user = auth_user
            self.open_main_window()
        else:
            QMessageBox.warning(self, "Erro", "Usuário ou senha inválidos")

    def open_main_window(self):
        self.main_win = MainWindow(user=self.authenticated_user)
        self.main_win.show()
        self.close()

    def on_open_cadastro(self):
        self.hide()
        cadastro = CadastroWindow(self)
        result = cadastro.exec()
        if result == 1:
            QMessageBox.information(self, "Cadastro", "Cadastro concluído! Faça login para continuar.")
        self.show()
