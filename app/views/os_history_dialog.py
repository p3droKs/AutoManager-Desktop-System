# views/os_history_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout
)
from controllers.os_controller import OSController
import datetime

class OSHistoryDialog(QDialog):
    def __init__(self, ordem_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Histórico da OS #{ordem_id}")
        self.ordem_id = ordem_id
        self.ctrl = OSController()
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel(f"<h3>Histórico da Ordem {self.ordem_id}</h3>"))

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Data/Hora", "Usuário", "Ação", "Status",
            "Prioridade", "Mecânico", "Valor (R$)", "Descrição"
        ])
        layout.addWidget(self.table)

        h = QHBoxLayout()
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.accept)
        h.addStretch()
        h.addWidget(btn_close)
        layout.addLayout(h)

    def _load_data(self):
        historicos = self.ctrl.listar_historico_os(self.ordem_id)
        self.table.setRowCount(len(historicos))

        for row, h in enumerate(historicos):
            # data/hora
            dt = getattr(h, "data", None)
            if isinstance(dt, datetime.datetime):
                dt_str = dt.strftime("%Y-%m-%d %H:%M")
            else:
                dt_str = str(dt or "")
            usuario = getattr(h, "usuario", "") or ""
            acao = getattr(h, "acao", "") or ""
            status = getattr(h, "status", "") or ""
            prioridade = getattr(h, "prioridade", "") or ""
            mecanico = getattr(h, "mecanico", "") or ""
            valor = getattr(h, "valor", 0.0) or 0.0
            descricao = getattr(h, "descricao", "") or ""

            values = [
                dt_str,
                usuario,
                acao,
                status,
                prioridade,
                mecanico,
                f"{float(valor):.2f}",
                descricao
            ]
            for col, v in enumerate(values):
                item = QTableWidgetItem(str(v))
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()
