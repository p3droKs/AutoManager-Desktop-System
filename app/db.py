from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///automanager.db"
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    import models.models as models  # garante import das classes
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
