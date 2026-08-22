import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Em produção (Render, Railway, etc.) essa variável vai apontar pro banco Postgres
# hospedado. Localmente, se você não definir nada, continua usando o clinic.db,
# do jeitinho que sempre funcionou no seu computador.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///clinic.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()