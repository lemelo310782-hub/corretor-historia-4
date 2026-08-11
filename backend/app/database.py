"""
Configuração da conexão com o banco de dados (SQLAlchemy).

Usamos SQLite na Fase 1 conforme solicitado. Como o app usa SQLAlchemy
como camada de abstração, migrar para PostgreSQL/MySQL no futuro exige
apenas trocar a DATABASE_URL em config.py — nenhum código de modelo muda.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency do FastAPI: entrega uma sessão de banco e garante o fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
