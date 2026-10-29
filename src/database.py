import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Obtiene la URL de la base de datos desde la variable de entorno de Docker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@localhost:5432/catalogo_db")

# Si se configuró PostgreSQL pero psycopg2 no está instalado en el host local, fallback transparente a SQLite
if DATABASE_URL.startswith("postgresql"):
    try:
        import psycopg2
        if DATABASE_URL.startswith("postgresql://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    except ImportError:
        DATABASE_URL = "sqlite:///./test_dev.db"

# Soporte para SQLite en entornos de pruebas locales sin Docker
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
