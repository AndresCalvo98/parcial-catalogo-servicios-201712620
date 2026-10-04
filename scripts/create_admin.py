import sys
import os

# Asegurar acceso a los módulos en src/
for _p in [os.path.dirname(os.path.abspath(__file__)), os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')), os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')), os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from database import SessionLocal
from models import Empresa, Area, Departamento, Seccion, Puesto, Usuario, ServicioNivel2
from auth import get_password_hash

def seed_demo_data():
    db = SessionLocal()
    print("=== CREANDO ESTRUCTURA ORGANIZACIONAL, USUARIOS Y ASIGNACIONES ===")
    
    try:
        # 1. Empresa (P04)
        empresa = db.query(Empresa).filter(Empresa.codigo == "USAC").first()
        if not empresa:
            empresa = Empresa(codigo="USAC", nombre="Universidad de San Carlos de Guatemala", activo=True)
            db.add(empresa)
            db.commit()
            db.refresh(empresa)

        # 2. Área
        area = db.query(Area).filter(Area.codigo == "DTI", Area.empresa_id == empresa.id).first()
        if not area:
            area = Area(codigo="DTI", nombre="Dirección General de Tecnología", empresa_id=empresa.id, activo=True)
            db.add(area)
            db.commit()
            db.refresh(area)

        # 3. Departamento
        depto = db.query(Departamento).filter(Departamento.codigo == "DDEV", Departamento.area_id == area.id).first()
        if not depto:
            depto = Departamento(codigo="DDEV", nombre="Departamento de Desarrollo e Innovación", area_id=area.id, activo=True)
            db.add(depto)
            db.commit()
            db.refresh(depto)

        # 4. Secciones
        sec_bnd = db.query(Seccion).filter(Seccion.codigo == "SEC-BND", Seccion.departamento_id == depto.id).first()
        if not sec_bnd:
            sec_bnd = Seccion(codigo="SEC-BND", nombre="Sección de Arquitectura y Backend", departamento_id=depto.id, activo=True)
            db.add(sec_bnd)

        sec_ops = db.query(Seccion).filter(Seccion.codigo == "SEC-OPS", Seccion.departamento_id == depto.id).first()
        if not sec_ops:
            sec_ops = Seccion(codigo="SEC-OPS", nombre="Sección de Operaciones e Infraestructura", departamento_id=depto.id, activo=True)
            db.add(sec_ops)

        db.commit()
        db.refresh(sec_bnd)
        db.refresh(sec_ops)

        # 5. Puestos
        puesto_lead = db.query(Puesto).filter(Puesto.codigo == "PST-LEAD", Puesto.seccion_id == sec_bnd.id).first()
        if not puesto_lead:
            puesto_lead = Puesto(codigo="PST-LEAD", nombre="Líder Técnico de Software", seccion_id=sec_bnd.id, activo=True)
            db.add(puesto_lead)

        puesto_sop = db.query(Puesto).filter(Puesto.codigo == "PST-SOP", Puesto.seccion_id == sec_ops.id).first()
        if not puesto_sop:
            puesto_sop = Puesto(codigo="PST-SOP", nombre="Especialista de Monitoreo y Soporte", seccion_id=sec_ops.id, activo=True)
            db.add(puesto_sop)

        db.commit()
        db.refresh(puesto_lead)
        db.refresh(puesto_sop)

        # 6. Usuarios de Demostración (3.1)
        # Administrador
        admin = db.query(Usuario).filter(Usuario.correo == "admin@demo.com").first()
        if not admin:
            admin = Usuario(
                nombre="Administrador General TI",
                correo="admin@demo.com",
                hashed_password=get_password_hash("admin123"),
                rol="administrador",
                puesto_id=puesto_lead.id,
                activo=True
            )
            db.add(admin)
        else:
            admin.puesto_id = puesto_lead.id

        # Consulta
        normal = db.query(Usuario).filter(Usuario.correo == "normal@demo.com").first()
        if not normal:
            normal = Usuario(
                nombre="Operador de Consulta",
                correo="normal@demo.com",
                hashed_password=get_password_hash("clave"),
                rol="consulta",
                puesto_id=puesto_sop.id,
                activo=True
            )
            db.add(normal)
        else:
            normal.puesto_id = puesto_sop.id

        db.commit()
        db.refresh(admin)
        db.refresh(normal)

        # 7. Asignaciones de Demostración (Requisito 3.3: Al menos 3 asignaciones válidas)
        servicios_a_asignar = db.query(ServicioNivel2).limit(3).all()
        if len(servicios_a_asignar) >= 3:
            # Asignación 1: Servicio 1 a Sección Backend y Usuario Admin
            servicios_a_asignar[0].seccion_id = sec_bnd.id
            servicios_a_asignar[0].usuario_id = admin.id

            # Asignación 2: Servicio 2 a Sección Backend (solo sección)
            servicios_a_asignar[1].seccion_id = sec_bnd.id
            servicios_a_asignar[1].usuario_id = admin.id

            # Asignación 3: Servicio 3 a Sección Operaciones y Usuario Consulta
            servicios_a_asignar[2].seccion_id = sec_ops.id
            servicios_a_asignar[2].usuario_id = normal.id

            db.commit()
            print("Tres asignaciones válidas vinculadas a servicios Nivel 2 exitosamente.")

        print("\n*** DATOS DE DEMOSTRACIÓN CONFIGURADOS EXITOSAMENTE ***")
        print("Credenciales de Evaluación listas:")
        print("  - Administrador: admin@demo.com / admin123")
        print("  - Consulta:      normal@demo.com / clave\n")

    except Exception as e:
        print(f"Error sembrando datos de demo: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
