# app/views/edit_os_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout, QMessageBox, QLabel
)
from controllers.os_controller import OSController
from controllers.auth_controller import AuthController

class EditOSDialog(QDialog):
    def __init__(self, os_obj, current_user=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Ordem de Serviço")
        self.os = os_obj
        self.current_user = current_user
        self.ctrl = OSController()
        self.auth_ctrl = AuthController()
        self._setup_ui()
        self._load_data()


    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        form = QFormLayout()

        self.input_descricao = QLineEdit()
        form.addRow("Descrição:", self.input_descricao)

        self.combo_status = QComboBox()
        self.combo_status.addItems(["ABERTA", "EM ANDAMENTO", "CONCLUIDA"])
        form.addRow("Status:", self.combo_status)

        self.combo_prioridade = QComboBox()
        self.combo_prioridade.addItems(["BAIXA", "MEDIA", "ALTA"])
        form.addRow("Prioridade:", self.combo_prioridade)

        # mecânico
        self.combo_mecanico = QComboBox()
        form.addRow("Mecânico responsável:", self.combo_mecanico)

        # veículo
        self.combo_veiculo = QComboBox()
        form.addRow("Veículo:", self.combo_veiculo)

        # novo: valor
        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("0.00")
        form.addRow("Valor (R$):", self.input_valor)

        layout.addLayout(form)

        h = QHBoxLayout()
        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self.on_save)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        h.addWidget(btn_save); h.addWidget(btn_cancel)
        layout.addLayout(h)

    def _load_data(self):
        self.input_descricao.setText(getattr(self.os, "descricao", "") or "")
        status = getattr(self.os, "status", "ABERTA")
        prioridade = getattr(self.os, "prioridade", "MEDIA")
        mecanico = getattr(self.os, "mecanico", "") or ""
        try:
            self.combo_status.setCurrentText(status)
        except Exception:
            self.combo_status.setCurrentIndex(0)
        try:
            self.combo_prioridade.setCurrentText(prioridade)
        except Exception:
            self.combo_prioridade.setCurrentIndex(1)

        # mecânicos
        self.combo_mecanico.clear()
        try:
            users = self.auth_ctrl.list_users()
            mecanicos = [u for u in users if (getattr(u, "role", "") or "").strip().lower() == "mecanico"]
            self.combo_mecanico.addItem("Nenhum", userData=None)
            sel_idx = 0
            for idx, u in enumerate(mecanicos, start=1):
                display = f"{u.nome or u.username} ({u.username})"
                self.combo_mecanico.addItem(display, userData=u.username)
                if u.username == mecanico:
                    sel_idx = idx
            self.combo_mecanico.setCurrentIndex(sel_idx)
        except Exception:
            self.combo_mecanico.addItem("Nenhum", userData=None)

        # veículos
        cliente_id = getattr(self.os, "cliente_id", None)
        self.combo_veiculo.clear()
        if cliente_id:
            veiculos = self.ctrl.listar_veiculos_por_cliente(cliente_id)
            sel = 0
            for idx, v in enumerate(veiculos):
                display = f"{v.placa} — {v.marca or ''} {v.modelo or ''}".strip()
                self.combo_veiculo.addItem(display, userData=v.id)
                if v.id == getattr(self.os, "veiculo_id", None):
                    sel = idx
            if self.combo_veiculo.count() > 0:
                self.combo_veiculo.setCurrentIndex(sel)
        else:
            self.combo_veiculo.addItem("Nenhum", userData=None)

        # valor
        valor = getattr(self.os, "valor", 0.0) or 0.0
        try:
            self.input_valor.setText(f"{float(valor):.2f}")
        except Exception:
            self.input_valor.setText("0.00")

    def on_save(self):
        descricao = self.input_descricao.text().strip()
        if not descricao:
            QMessageBox.warning(self, "Erro", "Descrição não pode ficar vazia.")
            return
        usuario = getattr(self.current_user, "username", None)
        status = self.combo_status.currentText()
        prioridade = self.combo_prioridade.currentText()
        mecanico_username = self.combo_mecanico.currentData()
        mecanico = mecanico_username if mecanico_username is not None else None
        veiculo_id = self.combo_veiculo.currentData()

        # validar valor
        val_text = self.input_valor.text().strip().replace(",", ".")
        try:
            valor = float(val_text) if val_text else 0.0
        except Exception:
            QMessageBox.warning(self, "Erro", "Valor inválido. Use números, ex: 150.00")
            return

        try:
            updated = self.ctrl.update_os(
                os_id=self.os.id,
                descricao=descricao,
                status=status,
                prioridade=prioridade,
                mecanico=mecanico,
                veiculo_id=veiculo_id,
                valor=valor,
                usuario=usuario
            )
            if updated is None:
                QMessageBox.warning(self, "Erro", "Ordem não encontrada.")
                self.reject(); return
            QMessageBox.information(self, "Ok", "Ordem atualizada com sucesso.")
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar OS: {ex}")
