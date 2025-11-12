from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QHBoxLayout, QComboBox)
from controllers.auth_controller import AuthController

class CadastroWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AutoManager - Cadastro")
        self.auth = AuthController()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Cadastro"))
        self.input_new_user = QLineEdit(); self.input_new_user.setPlaceholderText("Novo usuário (username)")
        self.input_new_nome = QLineEdit(); self.input_new_nome.setPlaceholderText("Nome (opcional)")
        self.input_new_pass = QLineEdit(); self.input_new_pass.setPlaceholderText("Senha")
        self.input_new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.combo_role = QComboBox()
        self.combo_role.addItems(["Mecanico", "Gerente", "Administrador"])
        btn_register = QPushButton("Cadastrar")
        btn_register.clicked.connect(self.on_register)
        layout.addWidget(self.input_new_user)
        layout.addWidget(self.input_new_nome)
        layout.addWidget(self.input_new_pass)
        layout.addWidget(QLabel("Papel"))
        layout.addWidget(self.combo_role)
        layout.addWidget(btn_register)

        h = QHBoxLayout()
        btn_cancel = QPushButton("Fechar")
        btn_cancel.clicked.connect(self.reject)
        h.addWidget(btn_cancel)
        layout.addLayout(h)

    def on_register(self):
        username = self.input_new_user.text().strip()
        nome = self.input_new_nome.text().strip()
        pwd = self.input_new_pass.text().strip()
        role = self.combo_role.currentText()
        if not username or not pwd:
            QMessageBox.warning(self, "Erro", "Usuário e senha são obrigatórios")
            return
        try:
            user = self.auth.register(username, nome, pwd, role)
            QMessageBox.information(self, "Ok", f"Usuário criado: {user.username} ({user.role})")
            self.input_new_user.clear()
            self.input_new_nome.clear()
            self.input_new_pass.clear()
            self.accept()
        except ValueError as ex:
            QMessageBox.warning(self, "Erro", str(ex))
