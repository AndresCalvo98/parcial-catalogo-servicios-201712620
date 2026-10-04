import sys
import os

# Asegurar acceso a los módulos en src/
for _p in [os.path.dirname(os.path.abspath(__file__)), os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')), os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')), os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from database import engine, Base
import models

def init_database():
    print("Creando tablas en la base de datos PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("¡Tablas creadas exitosamente!")

if __name__ == "__main__":
    init_database()
