# app/views/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QListWidget, QMessageBox, QHBoxLayout,
    QFormLayout, QToolBar, QStackedWidget, QListWidgetItem,
    QTableView, QHeaderView, QDialog, QAbstractItemView,
    QFileDialog
)
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QAction
import datetime
import csv
from controllers.os_controller import OSController
from controllers.auth_controller import AuthController
from views.edit_os_dialog import EditOSDialog
from views.os_history_dialog import OSHistoryDialog

class OSTableModel(QAbstractTableModel):
    COLUMNS = [
        ("ID", "id"),
        ("Código", "codigo"),
        ("Descrição", "descricao"),
        ("Status", "status"),
        ("Prioridade", "prioridade"),
        ("Cliente", "cliente_nome"),
        ("Veículo", "veiculo_placa"),
        ("Mecânico", "mecanico"),
        ("Aberta Em", "aberta_em"),
    ]

    def __init__(self, rows=None, parent=None):
        super().__init__(parent)
        self._rows = rows or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.COLUMNS[section][0]
        return section + 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        attr = self.COLUMNS[col][1]
        item = self._rows[row]

        if role == Qt.DisplayRole:
            # support both object attributes and dicts
            val = getattr(item, attr, None) if hasattr(item, attr) else item.get(attr, None)
            if isinstance(val, datetime.datetime):
                return val.strftime("%Y-%m-%d %H:%M")
            return "" if val is None else str(val)

        if role == Qt.UserRole:
            # Return the underlying object for convenience
            return item

        return None

    def get_item(self, row_idx):
        if 0 <= row_idx < len(self._rows):
            return self._rows[row_idx]
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = rows or []
        self.endResetModel()


class MainWindow(QMainWindow):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AutoManager")
        self.resize(900, 600)
        self._apply_style()
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
        self.stack.addWidget(self.page_os)
        self.stack.addWidget(self.page_clients)
        self.stack.addWidget(self.page_vehicles)
        self.stack.addWidget(self.page_users)

        # Barra de menu / toolbar
        self._create_menu()

        # Inicial: mostrar OS
        self.show_os_page()

    def _apply_style(self):
        """
        Aplica um tema escuro agradável para a janela principal.
        """
        self.setStyleSheet("""
        QMainWindow {
            background-color: #0f172a;  /* fundo geral */
            color: #e5e7eb;
        }

        QWidget {
            background-color: #020617;
            color: #e5e7eb;
        }

        QToolBar {
            background-color: #020617;
            spacing: 8px;
            padding: 4px 8px;
            border: none;
        }

        QToolBar QToolButton {
            background-color: transparent;
            color: #e5e7eb;
            padding: 4px 8px;
            border-radius: 6px;
        }

        QToolBar QToolButton:hover {
            background-color: #1f2937;
        }

        QMenuBar {
            background-color: #020617;
            color: #e5e7eb;
        }

        QMenuBar::item:selected {
            background-color: #1f2937;
        }

        QMenu {
            background-color: #020617;
            color: #e5e7eb;
            border: 1px solid #1f2937;
        }

        QMenu::item:selected {
            background-color: #1f2937;
        }

        QPushButton {
            background-color: #2563eb;
            color: #f9fafb;
            border-radius: 6px;
            padding: 6px 12px;
            border: none;
            font-weight: 500;
        }

        QPushButton:hover {
            background-color: #1d4ed8;
        }

        QPushButton:pressed {
            background-color: #1e40af;
        }

        QPushButton:disabled {
            background-color: #374151;
            color: #9ca3af;
        }

        QLineEdit, QComboBox {
            background-color: #020617;
            border: 1px solid #374151;
            border-radius: 4px;
            padding: 4px 8px;
            color: #e5e7eb;
            selection-background-color: #2563eb;
        }

        QLineEdit::placeholder {
            color: #6b7280;
        }

        QComboBox::drop-down {
            border: none;
        }

        QComboBox QAbstractItemView {
            background-color: #020617;
            border: 1px solid #374151;
            color: #e5e7eb;
            selection-background-color: #2563eb;
        }

        QLabel#pageTitle {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #f9fafb;
        }

        QLabel {
            color: #e5e7eb;
        }

        QListWidget {
            background-color: #020617;
            border: 1px solid #374151;
            border-radius: 4px;
        }

        QListWidget::item:selected {
            background-color: #1f2937;
            color: #f9fafb;
        }

        QTableView {
            background-color: #020617;
            gridline-color: #374151;
            border: 1px solid #374151;
            border-radius: 4px;
            selection-background-color: #2563eb;
            selection-color: #f9fafb;
        }

        QHeaderView::section {
            background-color: #020617;
            color: #e5e7eb;
            padding: 4px 6px;
            border: none;
            border-bottom: 1px solid #374151;
            font-weight: 600;
        }

        QScrollBar:vertical, QScrollBar:horizontal {
            background: #020617;
            border: none;
            width: 10px;
            margin: 0px;
        }

        QScrollBar::handle {
            background: #4b5563;
            border-radius: 5px;
        }

        QScrollBar::handle:hover {
            background: #6b7280;
        }

        QScrollBar::add-line, QScrollBar::sub-line {
            background: none;
            border: none;
        }
        """)


    # ---------------------------
    # Menu / Toolbar
    # ---------------------------
    def _create_menu(self):
        menubar = self.menuBar()
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

        self.act_users = QAction("Usuários", self)
        self.act_users.triggered.connect(self.show_users_page)
        self.act_users.setEnabled(self._current_user_is_admin())
        menu_opcoes.addAction(self.act_users)

        toolbar = QToolBar("Principal")
        self.addToolBar(toolbar)
        toolbar.addAction(self.act_os)
        toolbar.addAction(self.act_clients)
        toolbar.addAction(self.act_vehicles)
        toolbar.addAction(self.act_users)

    def _current_user_is_admin(self) -> bool:
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
        if not self._current_user_is_admin():
            QMessageBox.warning(self, "Acesso negado", "Acesso restrito a Administradores.")
            return
        self.stack.setCurrentWidget(self.page_users)
        self.load_users_list()

    # ---------------------------
    # OS Page (QTableView)
    # ---------------------------
    def _build_os_page(self):
        w = QWidget()
        layout = QVBoxLayout()
        w.setLayout(layout)

        title = QLabel("Ordens de Serviço")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        form = QFormLayout()
        self.os_cliente_combo = QComboBox()
        self.os_veiculo_combo = QComboBox()
        self.os_descricao = QLineEdit()
        self.os_valor = QLineEdit()
        self.os_valor.setPlaceholderText("0.00")
        form.addRow("Cliente:", self.os_cliente_combo)
        form.addRow("Veículo:", self.os_veiculo_combo)
        form.addRow("Descrição:", self.os_descricao)
        form.addRow("Valor (R$):", self.os_valor)
        layout.addLayout(form)

        # buttons: criar, editar, refresh
        btn_layout = QHBoxLayout()
        btn_create = QPushButton("Criar OS")
        btn_create.clicked.connect(self.on_criar_os)

        role = getattr(self.user, "role", "") if hasattr(self, "user") else ""
        if str(role).strip().lower() == "mecanico":
            btn_create.setEnabled(False)


        self.btn_edit_os = QPushButton("Editar OS")
        self.btn_edit_os.clicked.connect(self.on_edit_os)
        self.btn_edit_os.setEnabled(False)

        self.btn_history_os = QPushButton("Histórico")
        self.btn_history_os.clicked.connect(self.on_ver_historico_os)
        self.btn_history_os.setEnabled(False)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_os_list)

        btn_export = QPushButton("Exportar CSV")
        btn_export.clicked.connect(self.export_os_csv)
        btn_layout.addWidget(btn_export)

        btn_layout.addWidget(btn_create)
        btn_layout.addWidget(self.btn_edit_os)
        btn_layout.addWidget(self.btn_history_os)
        btn_layout.addWidget(btn_refresh)
        layout.addLayout(btn_layout)

        # Table view
        layout.addWidget(QLabel("Lista de Ordens:"))
        self.os_table = QTableView()
        self.os_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.os_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.os_table.horizontalHeader().setStretchLastSection(True)
        self.os_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.os_model = OSTableModel(rows=[])
        self.os_table.setModel(self.os_model)
        # escondendo ID (coluna 0) para o usuário
        self.os_table.setColumnHidden(0, True)
        # seleção
        self.os_table.selectionModel().selectionChanged.connect(self._on_os_table_selection_changed)
        # double click -> edit
        self.os_table.doubleClicked.connect(lambda _: self.on_edit_os())

        layout.addWidget(self.os_table)

        # delete button
        del_layout = QHBoxLayout()
        self.btn_delete_os = QPushButton("Excluir Ordem Selecionada")
        self.btn_delete_os.clicked.connect(self.on_excluir_os_table)
        self.btn_delete_os.setEnabled(False)
        del_layout.addWidget(self.btn_delete_os)
        layout.addLayout(del_layout)

        return w

    def _on_os_table_selection_changed(self, selected, deselected):
        has_sel = False
        try:
            has_sel = self.os_table.selectionModel().hasSelection()
        except Exception:
            has_sel = False
        self.btn_delete_os.setEnabled(has_sel)
        self.btn_edit_os.setEnabled(has_sel)
        self.btn_history_os.setEnabled(has_sel)

    def on_ver_historico_os(self):
        sel = self.os_table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(self, "Histórico", "Selecione uma ordem para ver o histórico.")
            return
        row_idx = sel[0].row()
        item = self.os_model.get_item(row_idx)
        os_id = getattr(item, "id", None) if hasattr(item, "id") else item.get("id")
        if not os_id:
            QMessageBox.warning(self, "Histórico", "Não foi possível identificar a OS selecionada.")
            return

        dlg = OSHistoryDialog(os_id, parent=self)
        dlg.exec()

    def load_clients_in_os_page(self):
        try:
            self.os_cliente_combo.currentIndexChanged.disconnect()
        except Exception:
            pass

        self.os_cliente_combo.clear()
        clientes = self.controller.listar_clientes()
        for c in clientes:
            self.os_cliente_combo.addItem(f"{c.nome}", userData=c.id)

        self._os_update_vehicles_from_client(0)
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
        """
        Carrega ordens via controller, enriquece com cliente_nome e veiculo_placa
        e atualiza o model da tabela.
        """
        ordens = self.controller.listar_os()  # lista de objetos OrdemServico
        enriched = []

        # carregar clientes para lookup rápido
        try:
            clientes = self.controller.listar_clientes()
            clientes_map = {c.id: c for c in clientes}
        except Exception:
            clientes_map = {}

        # para cada ordem, buscar placa/nome para exibição
        for o in ordens:
            cliente_nome = ""
            veiculo_placa = ""
            try:
                cliente = clientes_map.get(getattr(o, "cliente_id", None))
                if cliente:
                    cliente_nome = cliente.nome
            except Exception:
                cliente_nome = ""

            try:
                # listar veiculos do cliente e procurar por id
                veiculos = self.controller.listar_veiculos_por_cliente(getattr(o, "cliente_id", None))
                veiculo = next((v for v in veiculos if v.id == getattr(o, "veiculo_id", None)), None)
                if veiculo:
                    veiculo_placa = veiculo.placa
            except Exception:
                veiculo_placa = ""

            # anexa atributos (SQLModel aceita setattr)
            try:
                setattr(o, "cliente_nome", cliente_nome)
                setattr(o, "veiculo_placa", veiculo_placa)
            except Exception:
                # se não der, transforma em dict
                o = {
                    "id": getattr(o, "id", None),
                    "codigo": getattr(o, "codigo", ""),
                    "descricao": getattr(o, "descricao", ""),
                    "status": getattr(o, "status", ""),
                    "prioridade": getattr(o, "prioridade", ""),
                    "cliente_nome": cliente_nome,
                    "veiculo_placa": veiculo_placa,
                    "mecanico": getattr(o, "mecanico", ""),
                    "aberta_em": getattr(o, "aberta_em", None),
                }
            enriched.append(o)

        self.os_model.set_rows(enriched)
        # esconder ID caso tenha mudado o model
        try:
            self.os_table.setColumnHidden(0, True)
        except Exception:
            pass

        # reset buttons
        self.btn_delete_os.setEnabled(False)
        self.btn_edit_os.setEnabled(False)

    def on_criar_os(self):
        client_id = self.os_cliente_combo.currentData()
        veiculo_id = self.os_veiculo_combo.currentData()
        descricao = self.os_descricao.text().strip()
        val_text = self.os_valor.text().strip().replace(",", ".")
        try:
            valor = float(val_text) if val_text else 0.0
        except Exception:
            QMessageBox.warning(self, "Erro", "Valor inválido. Use número como 150.00")
            return

        if not client_id or not veiculo_id or not descricao:
            QMessageBox.warning(self, "Erro", "Preencha cliente, veículo e descrição.")
            return

        username = getattr(self.user, "username", None)
        role = getattr(self.user, "role", None)

        try:
            osr = self.controller.criar_os(
                client_id,
                veiculo_id,
                descricao,
                valor=valor,
                usuario=username,
                role=role,
            )
            QMessageBox.information(self, "Ok", f"Ordem criada: {osr.codigo}")
            self.os_descricao.clear()
            self.os_valor.clear()
            self.load_os_list()
        except PermissionError as ex:
            QMessageBox.warning(self, "Acesso negado", str(ex))
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao criar OS: {ex}")


    def on_edit_os(self):
        sel = self.os_table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(self, "Erro", "Selecione uma ordem para editar.")
            return
        row_idx = sel[0].row()
        item = self.os_model.get_item(row_idx)
        os_id = getattr(item, "id", None) if hasattr(item, "id") else item.get("id")
        os_obj = self.controller.get_os_by_id(os_id)
        if not os_obj:
            QMessageBox.warning(self, "Erro", "Ordem não encontrada.")
            self.load_os_list()
            return
        dlg = EditOSDialog(os_obj, current_user=self.user, parent=self)
        res = dlg.exec()
        if res == QDialog.Accepted:
            self.load_os_list()

    def on_excluir_os_table(self):
        sel = self.os_table.selectionModel().selectedRows()
        if not sel:
            return
        row_idx = sel[0].row()
        item = self.os_model.get_item(row_idx)
        os_id = getattr(item, "id", None) if hasattr(item, "id") else item.get("id")
        codigo = getattr(item, "codigo", "") if hasattr(item, "codigo") else item.get("codigo", "")

        confirm = QMessageBox.question(self, "Confirmar", f"Excluir a ordem {codigo}?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return

        role = getattr(self.user, "role", None)
        username = getattr(self.user, "username", None)

        try:
            ok = self.controller.delete_os(os_id, role=role, usuario=username)
            if ok:
                QMessageBox.information(self, "Ok", "Ordem excluída.")
                self.load_os_list()
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível excluir a ordem.")
        except PermissionError as ex:
            QMessageBox.warning(self, "Acesso negado", str(ex))
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir ordem: {ex}")

    def export_os_csv(self):
        ordens = self.controller.listar_os()
        if not ordens:
            QMessageBox.information(self, "Exportar CSV", "Nenhuma ordem para exportar.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "ordens_servico.csv", "CSV Files (*.csv)")
        if not path:
            return

        try:
            # carregar lookup de clientes/veiculos para human readable
            clientes = {c.id: c.nome for c in self.controller.listar_clientes()}
            rows = []
            for o in ordens:
                cliente_nome = clientes.get(getattr(o, "cliente_id", None), "")
                # tentar placa do veículo
                veiculo_placa = ""
                try:
                    veiculos = self.controller.listar_veiculos_por_cliente(getattr(o, "cliente_id", None))
                    v = next((v for v in veiculos if v.id == getattr(o, "veiculo_id", None)), None)
                    if v:
                        veiculo_placa = v.placa
                except Exception:
                    veiculo_placa = ""

                rows.append({
                    "id": getattr(o, "id", None),
                    "codigo": getattr(o, "codigo", ""),
                    "descricao": getattr(o, "descricao", ""),
                    "status": getattr(o, "status", ""),
                    "prioridade": getattr(o, "prioridade", ""),
                    "cliente": cliente_nome,
                    "veiculo": veiculo_placa,
                    "mecanico": getattr(o, "mecanico", "") or "",
                    "valor": f"{(getattr(o, 'valor', 0.0) or 0.0):.2f}",
                    "aberta_em": getattr(o, "aberta_em", ""),
                })

            # escrever CSV
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["id","codigo","descricao","status","prioridade","cliente","veiculo","mecanico","valor","aberta_em"])
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)

            QMessageBox.information(self, "Exportar CSV", f"Exportado com sucesso: {path}")
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {ex}")


    # ---------------------------
    # Clientes Page
    # ---------------------------
    def _build_clients_page(self):
        w = QWidget()
        layout = QVBoxLayout()
        w.setLayout(layout)

        title = QLabel("Clientes")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

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
        self.load_clients_in_os_page()

    def load_clients_list(self):
        self.clients_list.clear()
        clientes = self.controller.listar_clientes()
        for c in clientes:
            item = QListWidgetItem(f"{c.nome} — {c.documento or ''}")
            item.setData(Qt.UserRole, c.id)
            self.clients_list.addItem(item)

    def on_cliente_selected(self, current, previous):
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
                self.load_clients_in_os_page()
                self.load_clients_in_vehicle_page()
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
        w = QWidget()
        layout = QVBoxLayout()
        w.setLayout(layout)

        title = QLabel("Veículos")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

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

        self.btn_delete_vehicle = QPushButton("Excluir Veículo Selecionado")
        self.btn_delete_vehicle.clicked.connect(self.on_delete_vehicle)
        self.btn_delete_vehicle.setEnabled(False)

        btn_refresh_vehicles = QPushButton("Refresh")
        btn_refresh_vehicles.clicked.connect(self.load_vehicles_list)

        btn_layout.addWidget(btn_add_vehicle)
        btn_layout.addWidget(self.btn_delete_vehicle)
        btn_layout.addWidget(btn_refresh_vehicles)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Lista de Veículos"))
        self.vehicles_list = QListWidget()
        layout.addWidget(self.vehicles_list)

        # habilitar/desabilitar botão conforme seleção e papel
        self.vehicles_list.currentItemChanged.connect(self.on_vehicle_selected)

        return w

    def on_vehicle_selected(self, current, previous):
        """
        Habilita o botão de exclusão apenas se houver veículo selecionado
        E se o usuário for Administrador ou Gerente.
        """
        if current is None:
            self.btn_delete_vehicle.setEnabled(False)
            return

        role = getattr(self.user, "role", "") or ""
        r = str(role).strip().lower()
        if r in ("administrador", "gerente"):
            self.btn_delete_vehicle.setEnabled(True)
        else:
            # Mecânico (ou outro papel) não pode excluir
            self.btn_delete_vehicle.setEnabled(False)

    def on_delete_vehicle(self):
        item = self.vehicles_list.currentItem()
        if not item:
            return

        veiculo_id = item.data(Qt.UserRole)
        texto = item.text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Deseja realmente excluir o veículo:\n{texto}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        role = getattr(self.user, "role", None)
        username = getattr(self.user, "username", None)

        try:
            ok = self.controller.delete_veiculo(veiculo_id, role=role, usuario=username)
            if ok:
                QMessageBox.information(self, "Ok", "Veículo excluído com sucesso.")
                self.load_vehicles_list()
                # atualizar combos de OS e de veículos (se necessário)
                self.load_clients_in_os_page()
            else:
                QMessageBox.warning(self, "Erro", "Veículo não encontrado.")
        except ValueError as ex:
            # regra de negócio: veículo com OS vinculada
            QMessageBox.warning(self, "Erro", str(ex))
        except PermissionError as ex:
            # mecânico ou outro papel sem permissão
            QMessageBox.warning(self, "Acesso negado", str(ex))
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir veículo: {ex}")


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

        # nenhum selecionado após recarregar
        if hasattr(self, "btn_delete_vehicle"):
            self.btn_delete_vehicle.setEnabled(False)


    # ---------------------------
    # Users Page (usa AuthController)
    # ---------------------------
    def _build_users_page(self):
        w = QWidget(); layout = QVBoxLayout(); w.setLayout(layout)

        title = QLabel("Usuários")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

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

        if not self._current_user_is_admin():
            self.u_username.setEnabled(False)
            self.u_name.setEnabled(False)
            self.u_password.setEnabled(False)
            self.u_role.setEnabled(False)
            self.btn_add_user.setEnabled(False)
            self.btn_delete_user.setEnabled(False)

        self.users_list.currentItemChanged.connect(self.on_user_selected)

        return w

    def on_add_user(self):
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
        if current is None:
            self.btn_delete_user.setEnabled(False)
            return
        if not self._current_user_is_admin():
            self.btn_delete_user.setEnabled(False)
            return
        selected_id = current.data(Qt.UserRole)
        current_admin_id = getattr(self.user, "id", None)
        if current_admin_id is not None and selected_id == current_admin_id:
            self.btn_delete_user.setEnabled(False)
            return
        self.btn_delete_user.setEnabled(True)

    def on_delete_user(self):
        item = self.users_list.currentItem()
        if not item:
            return
        user_id = item.data(Qt.UserRole)
        username_display = item.text().split(" — ")[0]
        confirm = QMessageBox.question(self, "Confirmar", f"Excluir o usuário '{username_display}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        try:
            ok = self.auth_controller.delete_user(user_id)
            if ok:
                QMessageBox.information(self, "Ok", "Usuário excluído.")
                self.load_users_list()
            else:
                QMessageBox.warning(self, "Erro", "Usuário não encontrado ou não pôde ser excluído.")
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir usuário: {ex}")
