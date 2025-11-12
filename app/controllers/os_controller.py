from db import get_session
from models.models import Cliente, Veiculo, OrdemServico
from sqlmodel import select
import datetime

class OSController:
    def __init__(self):
        pass

    def criar_cliente(self, nome, documento=None, telefone=None, email=None):
        with get_session() as s:
            c = Cliente(nome=nome, documento=documento, telefone=telefone, email=email)
            s.add(c); s.commit(); s.refresh(c)
            return c

    def listar_clientes(self):
        with get_session() as s:
            return s.exec(select(Cliente)).all()

    def criar_veiculo(self, cliente_id, placa, marca=None, modelo=None, ano=None):
        with get_session() as s:
            v = Veiculo(placa=placa, marca=marca, modelo=modelo, ano=ano, cliente_id=cliente_id)
            s.add(v); s.commit(); s.refresh(v)
            return v

    def listar_veiculos_por_cliente(self, cliente_id):
        with get_session() as s:
            return s.exec(select(Veiculo).where(Veiculo.cliente_id == cliente_id)).all()

    def criar_os(self, cliente_id, veiculo_id, descricao, prioridade="MEDIA", mecanico=None):
        with get_session() as s:
            codigo = f"OS-{datetime.datetime.utcnow():%Y%m%d%H%M%S}"
            osr = OrdemServico(codigo=codigo, descricao=descricao, cliente_id=cliente_id,
                               veiculo_id=veiculo_id, prioridade=prioridade, mecanico=mecanico)
            s.add(osr); s.commit(); s.refresh(osr)
            return osr

    def listar_os(self):
        with get_session() as s:
            return s.exec(select(OrdemServico)).all()
