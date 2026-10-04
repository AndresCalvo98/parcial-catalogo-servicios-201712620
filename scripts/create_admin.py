from database import SessionLocal
from models import Usuario, Puesto, Seccion, Departamento, Area, Empresa
from auth import get_password_hash

db = SessionLocal()

# 1. Crear jerarquia organizacional (Requisito P04)
empresa = db.query(Empresa).first()
if not empresa:
    empresa = Empresa(codigo="USAC", nombre="Universidad de San Carlos")
    db.add(empresa)
    db.commit()
    db.refresh(empresa)

area = db.query(Area).first()
if not area:
    area = Area(codigo="IT", nombre="Dirección de Tecnología", empresa_id=empresa.id)
    db.add(area)
    db.commit()
    db.refresh(area)

depto = db.query(Departamento).first()
if not depto:
    depto = Departamento(codigo="DEV", nombre="Desarrollo de Software", area_id=area.id)
    db.add(depto)
    db.commit()
    db.refresh(depto)

seccion = db.query(Seccion).first()
if not seccion:
    seccion = Seccion(codigo="BND", nombre="Backend", departamento_id=depto.id)
    db.add(seccion)
    db.commit()
    db.refresh(seccion)

puesto = db.query(Puesto).first()
if not puesto:
    puesto = Puesto(codigo="ING", nombre="Ingeniero de Software", seccion_id=seccion.id)
    db.add(puesto)
    db.commit()
    db.refresh(puesto)

# 2. Crear usuario Administrador
admin = db.query(Usuario).filter(Usuario.correo == "admin@demo.com").first()
if not admin:
    admin = Usuario(
        nombre="Administrador del Sistema",
        correo="admin@demo.com",
        hashed_password=get_password_hash("admin123"),
        rol="administrador",
        puesto_id=puesto.id
    )
    db.add(admin)
    db.commit()
    print("\n*** ¡ÉXITO! Jerarquía y Usuario creados ***")
    print("Usuario para login:")
    print(" - Correo: admin@demo.com")
    print(" - Clave:  admin123")
    print(" - Rol:    administrador\n")
else:
    print("\nEl usuario administrador ya existe en la base de datos.")

db.close()
