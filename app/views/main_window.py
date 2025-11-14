# app/views/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QListWidget, QMessageBox, QHBoxLayout,
    QFormLayout, QToolBar, QStackedWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from controllers.os_controller import OSController
from controllers.auth_controller import AuthController


class MainWindow(QMainWindow):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AutoManager")
        self.resize(900, 600)

        # usuário autenticado (instância retornada pelo AuthController)
        self.user = user or None
        self.controller = OSController()
        self.auth_controller = AuthController()

        # Central stacked widget (cada "página" é um widget)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Criar páginas
        self.page_os = self._build_os_page()
        self.page_clients = self._build_clients_page()
        self.page_vehicles = self._build_vehicles_page()
        self.page_users = self._build_users_page()

        # Adicionar páginas ao stack
        self.stack.addWidget(self.page_os)       # index 0
        self.stack.addWidget(self.page_clients)  # index 1
        self.stack.addWidget(self.page_vehicles) # index 2
        self.stack.addWidget(self.page_users)    # index 3

        # Barra de menu / toolbar
        self._create_menu()

        # Inicial: mostrar OS
        self.show_os_page()

    # ---------------------------
    # Menu / Toolbar
    # ---------------------------
    def _create_menu(self):
        menubar = self.menuBar()  # QMenuBar
        menu_opcoes = menubar.addMenu("Opções")

        self.act_os = QAction("OS", self)
        self.act_os.triggered.connect(self.show_os_page)
        menu_opcoes.addAction(self.act_os)

        self.act_clients = QAction("Clientes", self)
        self.act_clients.triggered.connect(self.show_clients_page)
        menu_opcoes.addAction(self.act_clients)

        self.act_vehicles = QAction("Veículos", self)
        self.act_vehicles.triggered.connect(self.show_vehicles_page)
        menu_opcoes.addAction(self.act_vehicles)

        # Ação Usuários: será habilitada apenas para Administrador
        self.act_users = QAction("Usuários", self)
        self.act_users.triggered.connect(self.show_users_page)
        is_admin = self._current_user_is_admin()
        self.act_users.setEnabled(is_admin)
        menu_opcoes.addAction(self.act_users)

        # Toolbar (atalhos rápidos)
        toolbar = QToolBar("Principal")
        self.addToolBar(toolbar)
        toolbar.addAction(self.act_os)
        toolbar.addAction(self.act_clients)
        toolbar.addAction(self.act_vehicles)
        toolbar.addAction(self.act_users)

    def _current_user_is_admin(self) -> bool:
        """Retorna True se o usuário autenticado for Administrador."""
        if not self.user:
            return False
        role = getattr(self.user, "role", None) or getattr(self.user, "Role", None) or ""
        try:
            return str(role).strip().lower() == "administrador"
        except Exception:
            return False

    # ---------------------------
    # Page switching helpers
    # ---------------------------
    def show_os_page(self):
        self.stack.setCurrentWidget(self.page_os)
        self.load_os_list()
        self.load_clients_in_os_page()

    def show_clients_page(self):
        self.stack.setCurrentWidget(self.page_clients)
        self.load_clients_list()

    def show_vehicles_page(self):
        self.stack.setCurrentWidget(self.page_vehicles)
        self.load_clients_in_vehicle_page()
        self.load_vehicles_list()

    def show_users_page(self):
        # checagem extra de segurança: bloqueia se não for admin
        if not self._current_user_is_admin():
            QMessageBox.warning(self, "Acesso negado", "Acesso restrito a Administradores.")
            return
        self.stack.setCurrentWidget(self.page_users)
        self.load_users_list()

    # ---------------------------
    # OS Page (lista, criar, excluir)
    # ---------------------------
    def _build_os_page(self):
        w = QWidget()
        layout = QVBoxLayout()
        w.setLayout(layout)

        layout.addWidget(QLabel("<h2>Ordens de Serviço</h2>"))

        form = QFormLayout()
        self.os_cliente_combo = QComboBox()
        self.os_veiculo_combo = QComboBox()
        self.os_descricao = QLineEdit()
        form.addRow("Cliente:", self.os_cliente_combo)
        form.addRow("Veículo:", self.os_veiculo_combo)
        form.addRow("Descrição:", self.os_descricao)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_create = QPushButton("Criar OS")
        btn_create.clicked.connect(self.on_criar_os)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_os_list)
        btn_layout.addWidget(btn_create)
        btn_layout.addWidget(btn_refresh)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Lista de Ordens:"))
        self.os_list = QListWidget()
        layout.addWidget(self.os_list)

        del_layout = QHBoxLayout()
        self.btn_delete_os = QPushButton("Excluir Ordem Selecionada")
        self.btn_delete_os.clicked.connect(self.on_excluir_os)
        self.btn_delete_os.setEnabled(False)
        del_layout.addWidget(self.btn_delete_os)
        layout.addLayout(del_layout)

        self.os_list.currentItemChanged.connect(self.on_os_selected)
        return w

    def load_clients_in_os_page(self):
        # desconecta sinal anterior para evitar múltiplas conexões
        try:
            self.os_cliente_combo.currentIndexChanged.disconnect()
        except Exception:
            pass

        self.os_cliente_combo.clear()
        clientes = self.controller.listar_clientes()
        for c in clientes:
            self.os_cliente_combo.addItem(f"{c.nome}", userData=c.id)

        # pre-load vehicles for selected client
        self._os_update_vehicles_from_client(0)
        # reconectar sinal
        self.os_cliente_combo.currentIndexChanged.connect(self._os_update_vehicles_from_client)

    def _os_update_vehicles_from_client(self, idx):
        self.os_veiculo_combo.clear()
        client_id = self.os_cliente_combo.currentData()
        if not client_id:
            return
        veiculos = self.controller.listar_veiculos_por_cliente(client_id)
        for v in veiculos:
            display = f"{v.placa} — {v.modelo or ''}"
            self.os_veiculo_combo.addItem(display, userData=v.id)

    def load_os_list(self):
        self.os_list.clear()
        ordens = self.controller.listar_os()
        for o in ordens:
            item = QListWidgetItem(f"{o.codigo} — {o.descricao} — {o.status}")
            item.setData(Qt.UserRole, o.id)
            self.os_list.addItem(item)
        self.btn_delete_os.setEnabled(False)

    def on_criar_os(self):
        client_id = self.os_cliente_combo.currentData()
        veiculo_id = self.os_veiculo_combo.currentData()
        descricao = self.os_descricao.text().strip()
        if not client_id or not veiculo_id or not descricao:
            QMessageBox.warning(self, "Erro", "Preencha cliente, veículo e descrição.")
            return
        try:
            osr = self.controller.criar_os(client_id, veiculo_id, descricao)
            QMessageBox.information(self, "Ok", f"Ordem criada: {osr.codigo}")
            self.os_descricao.clear()
            self.load_os_list()
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao criar OS: {ex}")

    def on_os_selected(self, current, previous):
        self.btn_delete_os.setEnabled(current is not None)

    def on_excluir_os(self):
        item = self.os_list.currentItem()
        if not item:
            return
        os_id = item.data(Qt.UserRole)
        confirm = QMessageBox.question(self, "Confirmar", "Excluir a ordem selecionada?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        ok = self.controller.delete_os(os_id)
        if ok:
            QMessageBox.information(self, "Ok", "Ordem excluída.")
            self.load_os_list()
        else:
            QMessageBox.warning(self, "Erro", "Não foi possível excluir a ordem.")

    # ---------------------------
    # Clientes Page
    # ---------------------------
    def _build_clients_page(self):
        w = QWidget()
        layout = QVBoxLayout()
        w.setLayout(layout)

        layout.addWidget(QLabel("<h2>Clientes</h2>"))

        form = QFormLayout()
        self.cl_nome = QLineEdit()
        self.cl_doc = QLineEdit()
        self.cl_tel = QLineEdit()
        form.addRow("Nome:", self.cl_nome)
        form.addRow("Documento:", self.cl_doc)
        form.addRow("Telefone:", self.cl_tel)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_add_client = QPushButton("Adicionar Cliente")
        btn_add_client.clicked.connect(self.on_add_client)

        btn_delete_client = QPushButton("Excluir Cliente Selecionado")
        btn_delete_client.clicked.connect(self.on_delete_client)
        btn_delete_client.setEnabled(False)

        btn_refresh_clients = QPushButton("Refresh")
        btn_refresh_clients.clicked.connect(self.load_clients_list)

        btn_layout.addWidget(btn_add_client)
        btn_layout.addWidget(btn_delete_client)
        btn_layout.addWidget(btn_refresh_clients)

        self.btn_delete_client = btn_delete_client

        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Lista de Clientes"))
        self.clients_list = QListWidget()
        layout.addWidget(self.clients_list)
        self.clients_list.currentItemChanged.connect(self.on_cliente_selected)
        return w

    def on_add_client(self):
        nome = self.cl_nome.text().strip()
        documento = self.cl_doc.text().strip() or None
        telefone = self.cl_tel.text().strip() or None
        if not nome:
            QMessageBox.warning(self, "Erro", "Nome é obrigatório")
            return
        c = self.controller.criar_cliente(nome, documento=documento, telefone=telefone)
        QMessageBox.information(self, "Ok", f"Cliente criado: {c.nome}")
        self.cl_nome.clear(); self.cl_doc.clear(); self.cl_tel.clear()
        self.load_clients_list()
        # also refresh OS page client combo
        self.load_clients_in_os_page()

    def load_clients_list(self):
        self.clients_list.clear()
        clientes = self.controller.listar_clientes()
        for c in clientes:
            item = QListWidgetItem(f"{c.nome} — {c.documento or ''}")
            item.setData(Qt.UserRole, c.id)
            self.clients_list.addItem(item)

    def on_cliente_selected(self, current, previous):
        """Habilita o botão excluir quando há seleção."""
        self.btn_delete_client.setEnabled(current is not None)

    def on_delete_client(self):
        item = self.clients_list.currentItem()
        if not item:
            return

        cliente_id = item.data(Qt.UserRole)
        nome_cliente = item.text().split(" — ")[0]

        confirm = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir o cliente '{nome_cliente}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            ok = self.controller.delete_cliente(cliente_id)
            if ok:
                QMessageBox.information(self, "Ok", "Cliente excluído com sucesso.")
                self.load_clients_list()
                self.load_clients_in_os_page()        # atualiza combos
                self.load_clients_in_vehicle_page()   # atualiza combos
            else:
                QMessageBox.warning(self, "Erro", "Cliente não encontrado.")
        except ValueError as ex:
            QMessageBox.warning(self, "Erro", str(ex))
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir cliente: {ex}")

    # ---------------------------
    # Vehicles Page
    # ---------------------------
    def _build_vehicles_page(self):
        w = QWidget(); layout = QVBoxLayout(); w.setLayout(layout)
        layout.addWidget(QLabel("<h2>Veículos</h2>"))
        form = QFormLayout()
        self.v_cliente_combo = QComboBox()
        self.v_placa = QLineEdit()
        self.v_marca = QLineEdit()
        self.v_modelo = QLineEdit()
        form.addRow("Cliente:", self.v_cliente_combo)
        form.addRow("Placa:", self.v_placa)
        form.addRow("Marca:", self.v_marca)
        form.addRow("Modelo:", self.v_modelo)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_add_vehicle = QPushButton("Adicionar Veículo")
        btn_add_vehicle.clicked.connect(self.on_add_vehicle)
        btn_refresh_vehicles = QPushButton("Refresh")
        btn_refresh_vehicles.clicked.connect(self.load_vehicles_list)
        btn_layout.addWidget(btn_add_vehicle); btn_layout.addWidget(btn_refresh_vehicles)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Lista de Veículos"))
        self.vehicles_list = QListWidget()
        layout.addWidget(self.vehicles_list)

        return w

    def load_clients_in_vehicle_page(self):
        self.v_cliente_combo.clear()
        clientes = self.controller.listar_clientes()
        for c in clientes:
            self.v_cliente_combo.addItem(f"{c.nome}", userData=c.id)

    def on_add_vehicle(self):
        client_id = self.v_cliente_combo.currentData()
        placa = self.v_placa.text().strip()
        marca = self.v_marca.text().strip() or None
        modelo = self.v_modelo.text().strip() or None
        if not client_id or not placa:
            QMessageBox.warning(self, "Erro", "Selecione cliente e informe a placa")
            return
        v = self.controller.criar_veiculo(client_id, placa, marca=marca, modelo=modelo)
        QMessageBox.information(self, "Ok", f"Veículo criado: {v.placa}")
        self.v_placa.clear(); self.v_marca.clear(); self.v_modelo.clear()
        self.load_vehicles_list()
        self.load_clients_in_os_page()

    def load_vehicles_list(self):
        self.vehicles_list.clear()
        clientes = self.controller.listar_clientes()
        for c in clientes:
            veiculos = self.controller.listar_veiculos_por_cliente(c.id)
            for v in veiculos:
                item = QListWidgetItem(f"{v.placa} — {c.nome} — {v.modelo or ''}")
                item.setData(Qt.UserRole, v.id)
                self.vehicles_list.addItem(item)

    # ---------------------------
    # Users Page (usa AuthController)
    # ---------------------------
    def _build_users_page(self):
        w = QWidget(); layout = QVBoxLayout(); w.setLayout(layout)
        layout.addWidget(QLabel("<h2>Usuários</h2>"))

        form = QFormLayout()
        self.u_username = QLineEdit()
        self.u_name = QLineEdit()
        self.u_password = QLineEdit(); self.u_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.u_role = QComboBox(); self.u_role.addItems(["Mecanico", "Gerente", "Administrador"])
        form.addRow("Usuário:", self.u_username)
        form.addRow("Nome:", self.u_name)
        form.addRow("Senha:", self.u_password)
        form.addRow("Papel:", self.u_role)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.btn_add_user = QPushButton("Cadastrar Usuário")
        self.btn_add_user.clicked.connect(self.on_add_user)
        btn_refresh_users = QPushButton("Refresh")
        btn_refresh_users.clicked.connect(self.load_users_list)
        btn_layout.addWidget(self.btn_add_user); btn_layout.addWidget(btn_refresh_users)

        # botão excluir usuário
        self.btn_delete_user = QPushButton("Excluir Usuário Selecionado")
        self.btn_delete_user.clicked.connect(self.on_delete_user)
        self.btn_delete_user.setEnabled(False)
        btn_layout.addWidget(self.btn_delete_user)

        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Lista de Usuários"))
        self.users_list = QListWidget()
        layout.addWidget(self.users_list)

        # Se o usuário atual não for admin, desabilitar o formulário de criação e exclusão
        if not self._current_user_is_admin():
            self.u_username.setEnabled(False)
            self.u_name.setEnabled(False)
            self.u_password.setEnabled(False)
            self.u_role.setEnabled(False)
            self.btn_add_user.setEnabled(False)
            self.btn_delete_user.setEnabled(False)

        # conectar seleção de usuário para habilitar/excluir botão
        self.users_list.currentItemChanged.connect(self.on_user_selected)

        return w

    def on_add_user(self):
        # segurança adicional: apenas admin pode cadastrar usuários
        if not self._current_user_is_admin():
            QMessageBox.warning(self, "Acesso negado", "Apenas Administradores podem cadastrar usuários.")
            return

        username = self.u_username.text().strip()
        nome = self.u_name.text().strip()
        senha = self.u_password.text().strip()
        role = self.u_role.currentText()
        if not username or not senha:
            QMessageBox.warning(self, "Erro", "Usuário e senha obrigatórios")
            return
        try:
            user = self.auth_controller.register(username, nome, senha, role)
            QMessageBox.information(self, "Ok", f"Usuário criado: {user.username}")
            self.u_username.clear(); self.u_name.clear(); self.u_password.clear()
            self.load_users_list()
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Não foi possível criar usuário: {ex}")

    def load_users_list(self):
        self.users_list.clear()
        try:
            users = self.auth_controller.list_users()
            for u in users:
                item = QListWidgetItem(f"{u.username} — {u.nome or ''} — {u.role}")
                item.setData(Qt.UserRole, u.id)
                self.users_list.addItem(item)
            self.btn_delete_user.setEnabled(False)
        except Exception as ex:
            QMessageBox.warning(self, "Aviso", f"Erro ao listar usuários: {ex}")

    def on_user_selected(self, current, previous):
        # habilita botão excluir apenas se item selecionado e se for admin
        if current is None:
            self.btn_delete_user.setEnabled(False)
            return
        if not self._current_user_is_admin():
            self.btn_delete_user.setEnabled(False)
            return
        # evita o admin deletar a si mesmo (opcional)
        selected_id = current.data(Qt.UserRole)
        current_admin_id = getattr(self.user, "id", None)
        if current_admin_id is not None and selected_id == current_admin_id:
            # desabilitar exclusão do próprio admin
            self.btn_delete_user.setEnabled(False)
            return
        self.btn_delete_user.setEnabled(True)

    def on_delete_user(self):
        # confirmação e chamada ao controller
        item = self.users_list.currentItem()
        if not item:
            return
        user_id = item.data(Qt.UserRole)
        username_display = item.text().split(" — ")[0]
        confirm = QMessageBox.question(self, "Confirmar", f"Excluir o usuário '{username_display}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        # chamada ao controller
        try:
            ok = self.auth_controller.delete_user(user_id)
            if ok:
                QMessageBox.information(self, "Ok", "Usuário excluído.")
                self.load_users_list()
            else:
                QMessageBox.warning(self, "Erro", "Usuário não encontrado ou não pôde ser excluído.")
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir usuário: {ex}")
