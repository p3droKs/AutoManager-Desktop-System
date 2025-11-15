# views/login_window.py
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from controllers.auth_controller import AuthController
from views.cadastro_window import CadastroWindow
from views.main_window import MainWindow


class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.auth = AuthController()

        self.setWindowTitle("AutoManager - Login")
        # tamanho agradável (não-fullscreen)
        self.setFixedSize(440, 340)

        self._setup_ui()
        self._apply_style()
        self._center_on_screen()

    # --------------------------
    # UI
    # --------------------------
    def _setup_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)
        self.setLayout(root)

        # Título
        title = QLabel("AutoManager")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignHCenter)
        # título com cor mais escura para melhor contraste
        title.setStyleSheet("color: #222222;")

        subtitle = QLabel("Sistema de Gerenciamento de Oficinas")
        subtitle.setAlignment(Qt.AlignHCenter)
        subtitle.setStyleSheet("color: #555555; font-size: 11pt;")

        root.addWidget(title)
        root.addWidget(subtitle)

        # Card central
        card = QFrame()
        card.setObjectName("loginCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)
        card.setLayout(card_layout)

        lbl_login = QLabel("Acesse sua conta")
        lbl_login.setAlignment(Qt.AlignHCenter)
        lbl_login.setStyleSheet("font-weight: 600; font-size: 11pt;")
        card_layout.addWidget(lbl_login)

        # Campo usuário
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuário")
        self.input_user.setClearButtonEnabled(True)

        # Campo senha
        self.input_pass = QLineEdit()
        self.input_pass.setPlaceholderText("Senha")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setClearButtonEnabled(True)

        card_layout.addWidget(self.input_user)
        card_layout.addWidget(self.input_pass)

        # Botões
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_login = QPushButton("Entrar")
        self.btn_login.clicked.connect(self.on_login)

        self.btn_register = QPushButton("Cadastrar")
        self.btn_register.clicked.connect(self.on_open_cadastro)

        btn_row.addWidget(self.btn_login)
        btn_row.addWidget(self.btn_register)

        card_layout.addLayout(btn_row)

        root.addWidget(card)
        root.addStretch()

        # Enter na senha -> login
        self.input_pass.returnPressed.connect(self.on_login)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #dde1e7;
            }

            #loginCard {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #c3c7cd;
            }

            QLabel {
                color: #222222;
            }

            QLineEdit {
                padding: 8px 10px;
                border-radius: 6px;
                border: 1px solid #999999;
                background: #f5f5f5;
                color: #222222;
                font-size: 10pt;
            }

            QLineEdit:focus {
                border: 1px solid #0066cc;
                background: #ffffff;
            }

            QLineEdit::placeholder {
                /* placeholder mais escuro */
                color: #555555;
            }

            QPushButton {
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid #0066cc;
                background-color: #0066cc;
                color: #ffffff;
                font-weight: 600;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #004c99;
            }
            QPushButton:disabled {
                background-color: #9bbbd9;
                border-color: #9bbbd9;
            }
        """)

    def _center_on_screen(self):
        # Centraliza a janela na tela
        frame_geom = self.frameGeometry()
        screen = self.screen()
        if screen is not None:
            center_point = screen.availableGeometry().center()
            frame_geom.moveCenter(center_point)
            self.move(frame_geom.topLeft())

    def showEvent(self, event):
        super().showEvent(event)
        # garante centralização mesmo após mostrar
        self._center_on_screen()

    # --------------------------
    # Ações
    # --------------------------
    def on_login(self):
        username = self.input_user.text().strip()
        password = self.input_pass.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Erro", "Informe usuário e senha.")
            return

        try:
            user = self.auth.authenticate(username, password)
        except ValueError as ex:
            QMessageBox.warning(self, "Erro", str(ex))
            return
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao autenticar: {ex}")
            return

        # se logou, abre MainWindow
        self.open_main_window(user)

    def on_open_cadastro(self):
        dlg = CadastroWindow(parent=self)
        dlg.exec()
        # após cadastro, volta o foco para o usuário
        self.input_user.setFocus()

    def open_main_window(self, user):
        # Esconde tela de login e abre a principal
        try:
            self.hide()
            self.main = MainWindow(user=user)
            self.main.show()
            # quando a main for fechada, fechamos o login também
            self.main.destroyed.connect(self.close)
        except Exception as ex:
            # se der erro ao abrir a MainWindow, mostramos e reexibimos o login
            QMessageBox.critical(self, "Erro", f"Erro ao abrir a tela principal: {ex}")
            self.show()
