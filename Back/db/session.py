from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.setting import settings

from sqlalchemy.orm import declarative_base

Base = declarative_base()
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(
    DATABASE_URL,
    echo=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()