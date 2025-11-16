# app/models/models.py
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
import datetime

class OrdemServicoHistorico(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ordem_id: int = Field(foreign_key="ordemservico.id")

    data: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    usuario: Optional[str] = None
    acao: str = "ATUALIZACAO"  # CRIACAO / ATUALIZACAO / EXCLUSAO

    status: Optional[str] = None
    prioridade: Optional[str] = None
    mecanico: Optional[str] = None
    valor: Optional[float] = None
    descricao: Optional[str] = None


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, nullable=False, unique=True)
    nome: Optional[str] = None
    password_hash: str = Field(nullable=False)
    role: str = Field(default="Mecanico")


class Cliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    documento: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    veiculos: List["Veiculo"] = Relationship(back_populates="cliente")


class Veiculo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    placa: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano: Optional[int] = None
    cliente_id: Optional[int] = Field(default=None, foreign_key="cliente.id")
    cliente: Optional[Cliente] = Relationship(back_populates="veiculos")


class OrdemServico(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str
    descricao: str
    status: str = "ABERTA"
    prioridade: str = "MEDIA"
    aberta_em: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    cliente_id: int = Field(foreign_key="cliente.id")
    veiculo_id: int = Field(foreign_key="veiculo.id")
    mecanico: Optional[str] = None
    valor: float = Field(default=0.0)
