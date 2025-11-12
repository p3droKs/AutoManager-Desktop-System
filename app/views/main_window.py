from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel,
                               QLineEdit, QPushButton, QComboBox, QListWidget, QMessageBox, QHBoxLayout)
from controllers.os_controller import OSController
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("AutoManager - Home")
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        layout = QVBoxLayout(); central.setLayout(layout)

        if self.user:
            nome = getattr(self.user, "nome", None) or getattr(self.user, "username", "Usuário")
            role = getattr(self.user, "role", "—")
            layout.addWidget(QLabel(f"Bem-vindo, {nome} ({role})"))
        else:
            layout.addWidget(QLabel("Bem-vindo, visitante"))

        layout.addWidget(QLabel("Criar Cliente"))
        self.input_nome = QLineEdit(); self.input_nome.setPlaceholderText("Nome do cliente")
        btn_criar_cliente = QPushButton("Criar Cliente")
        btn_criar_cliente.clicked.connect(self.on_criar_cliente)
        layout.addWidget(self.input_nome); layout.addWidget(btn_criar_cliente)

        layout.addWidget(QLabel("Selecionar Cliente"))
        self.combo_clientes = QComboBox(); self.combo_clientes.currentIndexChanged.connect(self.on_cliente_selecionado)
        layout.addWidget(self.combo_clientes)

        layout.addWidget(QLabel("Placa do veículo"))
        self.input_placa = QLineEdit()
        btn_criar_veiculo = QPushButton("Adicionar Veículo")
        btn_criar_veiculo.clicked.connect(self.on_criar_veiculo)
        layout.addWidget(self.input_placa); layout.addWidget(btn_criar_veiculo)

        layout.addWidget(QLabel("Criar Ordem de Serviço"))
        self.input_descricao = QLineEdit(); self.input_descricao.setPlaceholderText("Descrição do serviço")
        btn_criar_os = QPushButton("Criar OS")
        btn_criar_os.clicked.connect(self.on_criar_os)
        layout.addWidget(self.input_descricao); layout.addWidget(btn_criar_os)

        layout.addWidget(QLabel("Ordens de Serviço"))
        self.list_os = QListWidget()
        layout.addWidget(self.list_os)

        h = QHBoxLayout()
        btn_refresh = QPushButton("Refresh OS")
        btn_refresh.clicked.connect(self.load_os_list)
        h.addWidget(btn_refresh)
        layout.addLayout(h)

    def _load_clients(self):
        self.combo_clientes.clear()
        clientes = self.controller.listar_clientes()
        for c in clientes:
            self.combo_clientes.addItem(f"{c.id} - {c.nome}", userData=c.id)

    def on_criar_cliente(self):
        nome = self.input_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "Nome é obrigatório")
            return
        self.controller.criar_cliente(nome)
        self.input_nome.clear()
        self._load_clients()

    def on_cliente_selecionado(self, idx):
        pass

    def on_criar_veiculo(self):
        idx = self.combo_clientes.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Erro", "Selecione um cliente")
            return
        cliente_id = self.combo_clientes.currentData()
        placa = self.input_placa.text().strip()
        if not placa:
            QMessageBox.warning(self, "Erro", "Placa é obrigatória")
            return
        self.controller.criar_veiculo(cliente_id, placa)
        self.input_placa.clear()
        QMessageBox.information(self, "Ok", "Veículo criado")

    def on_criar_os(self):
        idx = self.combo_clientes.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Erro", "Selecione um cliente")
            return
        cliente_id = self.combo_clientes.currentData()
        veiculos = self.controller.listar_veiculos_por_cliente(cliente_id)
        if not veiculos:
            QMessageBox.warning(self, "Erro", "Cliente não tem veículo cadastrado")
            return
        veiculo_id = veiculos[0].id
        descricao = self.input_descricao.text().strip()
        if not descricao:
            QMessageBox.warning(self, "Erro", "Descrição é obrigatória")
            return
        osr = self.controller.criar_os(cliente_id, veiculo_id, descricao)
        self.input_descricao.clear()
        QMessageBox.information(self, "Ok", f"OS criada: {osr.codigo}")
        self.load_os_list()

    def load_os_list(self):
        self.list_os.clear()
        for o in self.controller.listar_os():
            self.list_os.addItem(f"{o.codigo} — {o.descricao} — {o.status}")
