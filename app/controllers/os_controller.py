# app/controllers/os_controller.py
from db import get_session
from models.models import Cliente, Veiculo, OrdemServico, OrdemServicoHistorico
from sqlmodel import select
import datetime

class OSController:
    def __init__(self):
        pass
    
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
                  usuario: str | None = None):
        with get_session() as s:
            osr = s.get(OrdemServico, os_id)
            if not osr:
                return None

            changed = False
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
                    osr.valor = v
                    changed = True

            if changed:
                s.add(osr)
                s.commit()
                s.refresh(osr)

                # histórico de atualização
                self._registrar_historico(s, osr, acao="ATUALIZACAO", usuario=usuario)
                s.commit()

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
                 usuario: str | None = None):
        with get_session() as s:
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

            # histórico de criação
            self._registrar_historico(s, osr, acao="CRIACAO", usuario=usuario)
            s.commit()

            return osr

    def listar_os(self):
        with get_session() as s:
            return s.exec(select(OrdemServico)).all()

    def get_os_by_id(self, os_id):
        with get_session() as s:
            return s.get(OrdemServico, os_id)

    def delete_os(self, os_id):
        with get_session() as s:
            osr = s.get(OrdemServico, os_id)
            if not osr:
                return False
            s.delete(osr)
            s.commit()
            return True
