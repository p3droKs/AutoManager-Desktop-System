# app/controllers/os_controller.py
from db import get_session
from models.models import Cliente, Veiculo, OrdemServico, OrdemServicoHistorico
from sqlmodel import select
import datetime

class OSController:
    def __init__(self):
        pass
    
    def delete_veiculo(self, veiculo_id: int, role: str | None = None, usuario: str | None = None) -> bool:
        with get_session() as s:
            v = s.get(Veiculo, veiculo_id)
            if not v:
                return False

            # regra de permissão: apenas Admin ou Gerente
            r = (role or "").strip().lower() if role else ""
            if r not in ("administrador", "gerente"):
                raise PermissionError("Apenas Administrador ou Gerente podem excluir veículos.")

            # ver se há OS vinculadas a este veículo
            os_vinculada = s.exec(
                select(OrdemServico).where(OrdemServico.veiculo_id == veiculo_id)
            ).first()
            if os_vinculada:
                raise ValueError("Não é possível excluir: existem Ordens de Serviço vinculadas a este veículo.")

            s.delete(v)
            s.commit()
            return True


    def _registrar_historico(self, s, osr: OrdemServico, acao: str, usuario: str | None = None):
        h = OrdemServicoHistorico(
            ordem_id=osr.id,
            usuario=usuario,
            acao=acao,
            status=osr.status,
            prioridade=osr.prioridade,
            mecanico=osr.mecanico,
            valor=osr.valor,
            descricao=osr.descricao,
        )
        s.add(h)

    def update_os(self, os_id: int, descricao: str = None, status: str = None,
              prioridade: str = None, mecanico: str = None,
              veiculo_id: int = None, valor: float = None,
              usuario: str | None = None, role: str | None = None):
        with get_session() as s:
            osr = s.get(OrdemServico, os_id)
            if not osr:
                return None

            # checa permissão para UPDATE em geral
            self._check_os_permission(osr, role=role, username=usuario, action="update")

            r = self._normalize_role(role)
            user = (usuario or "").strip()

            changed = False

            # Regras por papel:

            # 1) Administrador ou Gerente: podem alterar tudo
            if r in ("administrador", "gerente"):
                if descricao is not None and descricao.strip() != osr.descricao:
                    osr.descricao = descricao.strip(); changed = True
                if status is not None and status != osr.status:
                    osr.status = status; changed = True
                if prioridade is not None and prioridade != osr.prioridade:
                    osr.prioridade = prioridade; changed = True
                if mecanico is not None and mecanico != osr.mecanico:
                    osr.mecanico = mecanico; changed = True
                if veiculo_id is not None and veiculo_id != osr.veiculo_id:
                    osr.veiculo_id = veiculo_id; changed = True
                if valor is not None:
                    try:
                        v = float(valor)
                    except Exception:
                        v = 0.0
                    if v != osr.valor:
                        osr.valor = v; changed = True

            # 2) Mecânico: só pode alterar descrição e status da própria OS
            elif r == "mecanico":
                # aqui _check_os_permission já garantiu que osr.mecanico == user
                if status is not None and status != osr.status:
                    osr.status = status; changed = True
                if descricao is not None and descricao.strip() != osr.descricao:
                    osr.descricao = descricao.strip(); changed = True
                # qualquer tentativa de mudar outros campos é ignorada para esse papel

            else:
                # não deveria chegar aqui (já tratado em _check_os_permission)
                raise PermissionError("Usuário sem permissão para alterar ordens de serviço.")

            if changed:
                s.add(osr)
                s.commit()
                s.refresh(osr)

                # histórico
                try:
                    self._registrar_historico(s, osr, acao="ATUALIZACAO", usuario=usuario)
                    s.commit()
                except Exception:
                    pass

            return osr


    def listar_historico_os(self, ordem_id: int):
        with get_session() as s:
            stmt = select(OrdemServicoHistorico).where(
                OrdemServicoHistorico.ordem_id == ordem_id
            ).order_by(OrdemServicoHistorico.data.desc())
            return s.exec(stmt).all()


    def criar_cliente(self, nome, documento=None, telefone=None, email=None):
        with get_session() as s:
            c = Cliente(nome=nome, documento=documento, telefone=telefone, email=email)
            s.add(c); s.commit(); s.refresh(c)
            return c

    def listar_clientes(self):
        with get_session() as s:
            return s.exec(select(Cliente)).all()

    def delete_cliente(self, cliente_id: int):
        """
        Exclui um cliente somente se ele não possuir veículos ou ordens de serviço vinculados.
        Retorna:
            True  -> se excluiu
            False -> se não encontrou ou não pode excluir
        """
        with get_session() as s:
            cliente = s.get(Cliente, cliente_id)
            if not cliente:
                return False

            # Verificar se há veículos vinculados
            veiculos = s.exec(select(Veiculo).where(Veiculo.cliente_id == cliente_id)).all()
            if veiculos:
                raise ValueError("Não é possível excluir: o cliente possui veículos cadastrados.")

            # Verificar se há OS vinculadas
            ordens = s.exec(select(OrdemServico).where(OrdemServico.cliente_id == cliente_id)).all()
            if ordens:
                raise ValueError("Não é possível excluir: o cliente possui Ordens de Serviço vinculadas.")

            s.delete(cliente)
            s.commit()
            return True


    def criar_veiculo(self, cliente_id, placa, marca=None, modelo=None, ano=None):
        with get_session() as s:
            v = Veiculo(placa=placa, marca=marca, modelo=modelo, ano=ano, cliente_id=cliente_id)
            s.add(v); s.commit(); s.refresh(v)
            return v

    def listar_veiculos_por_cliente(self, cliente_id):
        with get_session() as s:
            return s.exec(select(Veiculo).where(Veiculo.cliente_id == cliente_id)).all()

    def criar_os(self, cliente_id, veiculo_id, descricao,
             prioridade="MEDIA", mecanico=None, valor: float = 0.0,
             usuario: str | None = None, role: str | None = None):
        with get_session() as s:
            # permissão de criação
            self._check_os_permission(osr=None, role=role, username=usuario, action="create")

            codigo = f"OS-{datetime.datetime.utcnow():%Y%m%d%H%M%S}"
            osr = OrdemServico(
                codigo=codigo,
                descricao=descricao,
                cliente_id=cliente_id,
                veiculo_id=veiculo_id,
                prioridade=prioridade,
                mecanico=mecanico,
                valor=float(valor or 0.0)
            )
            s.add(osr)
            s.commit()
            s.refresh(osr)

            # histórico de criação (se você já implementou)
            try:
                self._registrar_historico(s, osr, acao="CRIACAO", usuario=usuario)
                s.commit()
            except Exception:
                pass

            return osr


    def listar_os(self):
        with get_session() as s:
            return s.exec(select(OrdemServico)).all()

    def get_os_by_id(self, os_id):
        with get_session() as s:
            return s.get(OrdemServico, os_id)

    def delete_os(self, os_id: int, role: str | None = None, usuario: str | None = None):
        with get_session() as s:
            osr = s.get(OrdemServico, os_id)
            if not osr:
                return False

            # checa permissão
            self._check_os_permission(osr, role=role, username=usuario, action="delete")

            s.delete(osr)
            s.commit()

            # se quiser, registrar histórico de exclusão:
            # (nesse ponto seria melhor marcar como "REMOVIDA" em vez de apagar de fato)
            return True

    
    def _normalize_role(self, role: str | None) -> str:
        if not role:
            return ""
        return str(role).strip().lower()

    def _check_os_permission(self, osr, role: str | None, username: str | None, action: str):
        """
        action: 'create', 'update', 'delete'
        Levanta PermissionError se não tiver permissão.
        """
        r = self._normalize_role(role)
        user = (username or "").strip()

        # Admin pode tudo
        if r == "administrador":
            return

        if action == "create":
            # Só Admin ou Gerente podem criar OS
            if r not in ("administrador", "gerente"):
                raise PermissionError("Apenas Administrador ou Gerente podem criar ordens de serviço.")
            return

        if action == "delete":
            # Só Admin ou Gerente podem excluir OS
            if r not in ("administrador", "gerente"):
                raise PermissionError("Apenas Administrador ou Gerente podem excluir ordens de serviço.")
            return

        if action == "update":
            # Gerente pode editar qualquer OS
            if r == "gerente":
                return
            # Mecânico: só pode mexer nas OS atribuídas a ele
            if r == "mecanico":
                if not osr.mecanico or osr.mecanico != user:
                    raise PermissionError("Mecânico só pode alterar ordens atribuídas a ele.")
                return

            # outras roles (ou vazio) não podem atualizar
            raise PermissionError("Usuário sem permissão para alterar ordens de serviço.")
