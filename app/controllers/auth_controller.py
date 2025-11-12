# app/controllers/auth_controller.py (trecho adaptado)
from passlib.context import CryptContext
from db import get_session
from models.models import User
from sqlmodel import select

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt_sha256", "bcrypt"],
    deprecated="auto"
)

class AuthController:
    def register(self, username: str, nome: str, password: str, role: str = "Mecanico"):
        if not username or not password:
            raise ValueError("username and password required")
        with get_session() as s:
            exists = s.exec(select(User).where(User.username == username)).first()
            if exists:
                raise ValueError("username already exists")
            hashed = pwd_context.hash(password)   # usa bcrypt_sha256 por padrão
            user = User(username=username, nome=nome or username, password_hash=hashed, role=role)
            s.add(user); s.commit(); s.refresh(user)
            return user

    def authenticate(self, username: str, password: str):
        with get_session() as s:
            user = s.exec(select(User).where(User.username == username)).first()
            if not user:
                return None
            if pwd_context.verify(password, user.password_hash):
                # opcional: rehash se o esquema estiver obsoleto -> atualiza para o padrão
                if pwd_context.needs_update(user.password_hash):
                    user.password_hash = pwd_context.hash(password)
                    s.add(user); s.commit()
                return user
            return None
