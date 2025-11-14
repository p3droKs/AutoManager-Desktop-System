from sqlmodel import select
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from passlib.hash import bcrypt, bcrypt_sha256
from db import get_session
from models.models import User

# Permite autenticar hashes antigos e gerar novos seguros
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt_sha256", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4
)


class AuthController:
    def __init__(self):
        pass

    # ----------------------------------------------
    # CRIAR USUÁRIO
    # ----------------------------------------------
    def register(self, username: str, nome: str, password: str, role: str = "Mecanico"):
        if not username or not password:
            raise ValueError("username and password required")

        with get_session() as s:
            exists = s.exec(select(User).where(User.username == username)).first()
            if exists:
                raise ValueError("Usuário já existe")

            hashed = pwd_context.hash(password)
            user = User(username=username, nome=nome or username,
                        password_hash=hashed, role=role)
            s.add(user)
            s.commit()
            s.refresh(user)
            return user

    # ----------------------------------------------
    # AUTENTICAR
    # ----------------------------------------------
    def authenticate(self, username: str, password: str):
        """
        Tenta autenticar o usuário:
        1) tenta verificar com pwd_context (padrão: bcrypt_sha256/bcrypt)
        2) se UnknownHashError, tenta bcrypt_sha256 e bcrypt explicitamente
        3) como último recurso, compara plaintext (apenas para recuperação)
        Em caso de sucesso, re-hash com pwd_context e atualiza o DB.
        """
        with get_session() as s:
            user = s.exec(select(User).where(User.username == username)).first()
            if not user:
                return None

            ph = getattr(user, "password_hash", None) or ""

            # 1) tentativa normal com pwd_context
            try:
                if pwd_context.verify(password, ph):
                    # re-hash se necessário (upgrade de esquema)
                    if pwd_context.needs_update(ph):
                        user.password_hash = pwd_context.hash(password)
                        s.add(user); s.commit()
                    return user
            except UnknownHashError:
                # hash não reconhecido pelo pwd_context -> tentar fallbacks
                pass
            except Exception:
                # qualquer outro erro de verificação, falha com None
                return None

            # 2) tentativas explícitas de schemes conhecidos (fallback)
            try:
                if bcrypt_sha256.verify(password, ph):
                    # re-hash com o contexto padrão
                    user.password_hash = pwd_context.hash(password)
                    s.add(user); s.commit()
                    return user
            except Exception:
                pass

            try:
                if bcrypt.verify(password, ph):
                    user.password_hash = pwd_context.hash(password)
                    s.add(user); s.commit()
                    return user
            except Exception:
                pass

            # 3) fallback temporário: se o password_hash for exatamente a senha (texto puro)
            #    use isso APENAS para recuperar o acesso — será re-hashed em seguida.
            try:
                if ph == password:
                    user.password_hash = pwd_context.hash(password)
                    s.add(user); s.commit()
                    return user
            except Exception:
                pass

            # nada bateu -> autenticação falha
            return None

    # ----------------------------------------------
    # LISTAR USUÁRIOS
    # ----------------------------------------------
    def list_users(self):
        with get_session() as s:
            return s.exec(select(User)).all()

    # ----------------------------------------------
    # EXCLUIR USUÁRIO
    # ----------------------------------------------
    def delete_user(self, user_id: int):
        """
        Exclui um usuário pelo id.
        Retorna True se excluiu, False se não encontrado.
        """
        with get_session() as s:
            user = s.get(User, user_id)
            if not user:
                return False
            s.delete(user)
            s.commit()
            return True

