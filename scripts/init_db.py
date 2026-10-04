import os
from database import engine, Base
# Importar todos los modelos asegura que SQLAlchemy los registre antes de crear las tablas
import models

def init_db():
    print("Inicializando la estructura de la base de datos...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Todas las tablas (Estructura Organizacional y Catálogo) se han creado exitosamente.")
    except Exception as e:
        print(f"Error al crear las tablas: {e}")

if __name__ == "__main__":
    init_db()
