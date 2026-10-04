import os
import sys
import pytest
from fastapi.testclient import TestClient

# Asegurar acceso a src/ y scripts/
for _p in [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from main import app
from database import SessionLocal
import models
from auth import get_password_hash
from import_excel import import_data

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def setup_base_data(db_session):
    # Asegurar usuario administrador, consulta e inactivo para suite de pruebas
    admin = db_session.query(models.Usuario).filter(models.Usuario.correo == "admin@demo.com").first()
    if not admin:
        admin = models.Usuario(
            nombre="Admin Test",
            correo="admin@demo.com",
            hashed_password=get_password_hash("admin123"),
            rol="administrador",
            activo=True
        )
        db_session.add(admin)

    normal = db_session.query(models.Usuario).filter(models.Usuario.correo == "normal@demo.com").first()
    if not normal:
        normal = models.Usuario(
            nombre="Consulta Test",
            correo="normal@demo.com",
            hashed_password=get_password_hash("clave"),
            rol="consulta",
            activo=True
        )
        db_session.add(normal)

    inactivo = db_session.query(models.Usuario).filter(models.Usuario.correo == "inactivo@demo.com").first()
    if not inactivo:
        inactivo = models.Usuario(
            nombre="Inactivo Test",
            correo="inactivo@demo.com",
            hashed_password=get_password_hash("clave"),
            rol="consulta",
            activo=False
        )
        db_session.add(inactivo)

    # Nivel 1 base para pruebas
    n1 = db_session.query(models.ServicioNivel1).filter(models.ServicioNivel1.codigo == "N1-TEST").first()
    if not n1:
        n1 = models.ServicioNivel1(codigo="N1-TEST", nombre="Servicio Nivel 1 Test", activo=True)
        db_session.add(n1)

    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(normal)
    db_session.refresh(inactivo)
    db_session.refresh(n1)

    return {"admin": admin, "normal": normal, "inactivo": inactivo, "n1": n1}

def get_auth_token(username, password):
    res = client.post("/token", data={"username": username, "password": password})
    if res.status_code == 200:
        return res.json()["access_token"]
    return None

# =========================================================================
# ESCENARIOS DE ACEPTACIÓN OBLIGATORIOS (P01 - P12)
# =========================================================================

def test_P01_inicio_sesion_valido_e_invalido(setup_base_data):
    """P01: Inicio de sesión válido e inválido"""
    # Válido
    res_valido = client.post("/token", data={"username": "admin@demo.com", "password": "admin123"})
    assert res_valido.status_code == 200
    assert "access_token" in res_valido.json()
    assert res_valido.json()["rol"] == "administrador"

    # Inválido
    res_invalido = client.post("/token", data={"username": "admin@demo.com", "password": "password_erronea"})
    assert res_invalido.status_code == 401
    assert "incorrectos" in res_invalido.json()["detail"].lower()

def test_P02_acceso_sin_sesion_cierre_sesion_y_usuario_inactivo(setup_base_data):
    """P02: Acceso sin sesión, cierre de sesión y usuario inactivo"""
    # 1. Acceso sin sesión a recurso protegido
    res_sin_token = client.get("/servicios/")
    assert res_sin_token.status_code == 401

    # 2. Cierre de sesión
    token_admin = get_auth_token("admin@demo.com", "admin123")
    res_logout = client.post("/logout", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_logout.status_code == 200
    assert "correctamente" in res_logout.json()["message"]

    # 3. Usuario inactivo
    res_inactivo = client.post("/token", data={"username": "inactivo@demo.com", "password": "clave"})
    assert res_inactivo.status_code == 403
    assert "inactivo" in res_inactivo.json()["detail"].lower()

def test_P03_usuario_consulta_intenta_modificar_datos(setup_base_data):
    """P03: Usuario de consulta intenta modificar datos (rechazo en servidor; lectura permitida)"""
    token_normal = get_auth_token("normal@demo.com", "clave")
    headers = {"Authorization": f"Bearer {token_normal}"}

    # Lectura permitida
    res_get = client.get("/servicios/", headers=headers)
    assert res_get.status_code == 200

    # Intento de modificación / creación (Rechazo con 403)
    nuevo_servicio = {
        "codigo": "P03-HACK",
        "nombre": "Servicio Ilegal",
        "nivel1_id": setup_base_data["n1"].id
    }
    res_post = client.post("/servicios/", json=nuevo_servicio, headers=headers)
    assert res_post.status_code == 403
    assert "administrador" in res_post.json()["detail"].lower()

def test_P04_crear_jerarquia_y_asignar_usuario(setup_base_data, db_session):
    """P04: Crear una jerarquía organizacional completa y asignar un usuario"""
    # Aislamiento de pruebas: limpieza de registros previos con los mismos códigos
    u_prev = db_session.query(models.Usuario).filter(models.Usuario.correo == "jerarquia@demo.com").first()
    if u_prev:
        db_session.delete(u_prev)
        db_session.commit()
    pst_prev = db_session.query(models.Puesto).filter(models.Puesto.codigo == "PST-P04").first()
    if pst_prev:
        db_session.delete(pst_prev)
        db_session.commit()
    sec_prev = db_session.query(models.Seccion).filter(models.Seccion.codigo == "SEC-P04").first()
    if sec_prev:
        db_session.delete(sec_prev)
        db_session.commit()
    dep_prev = db_session.query(models.Departamento).filter(models.Departamento.codigo == "DEP-P04").first()
    if dep_prev:
        db_session.delete(dep_prev)
        db_session.commit()
    area_prev = db_session.query(models.Area).filter(models.Area.codigo == "ARE-P04").first()
    if area_prev:
        db_session.delete(area_prev)
        db_session.commit()
    emp_prev = db_session.query(models.Empresa).filter(models.Empresa.codigo == "EMP-P04").first()
    if emp_prev:
        db_session.delete(emp_prev)
        db_session.commit()

    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    # 1. Empresa
    res_emp = client.post("/empresas/", json={"codigo": "EMP-P04", "nombre": "Empresa P04"}, headers=headers)
    assert res_emp.status_code == 200
    emp_id = res_emp.json()["id"]

    # 2. Área
    res_area = client.post("/areas/", json={"codigo": "ARE-P04", "nombre": "Área P04", "empresa_id": emp_id}, headers=headers)
    assert res_area.status_code == 200
    area_id = res_area.json()["id"]

    # 3. Departamento
    res_dep = client.post("/departamentos/", json={"codigo": "DEP-P04", "nombre": "Depto P04", "area_id": area_id}, headers=headers)
    assert res_dep.status_code == 200
    dep_id = res_dep.json()["id"]

    # 4. Sección
    res_sec = client.post("/secciones/", json={"codigo": "SEC-P04", "nombre": "Sección P04", "departamento_id": dep_id}, headers=headers)
    assert res_sec.status_code == 200
    sec_id = res_sec.json()["id"]

    # 5. Puesto
    res_pue = client.post("/puestos/", json={"codigo": "PST-P04", "nombre": "Puesto P04", "seccion_id": sec_id}, headers=headers)
    assert res_pue.status_code == 200
    pue_id = res_pue.json()["id"]

    # 6. Asignar usuario
    res_user = client.post("/usuarios/", json={
        "nombre": "Usuario Jerarquía",
        "correo": "jerarquia@demo.com",
        "password": "clave",
        "rol": "consulta",
        "puesto_id": pue_id
    }, headers=headers)
    assert res_user.status_code == 200
    assert res_user.json()["puesto_id"] == pue_id

def test_P05_codigo_duplicado_o_referencia_inexistente(setup_base_data, db_session):
    """P05: Código duplicado o referencia inexistente rechazada con mensaje comprensible"""
    s_dup_prev = db_session.query(models.ServicioNivel2).filter(models.ServicioNivel2.codigo == "P05-DUP").first()
    if s_dup_prev:
        db_session.delete(s_dup_prev)
        db_session.commit()

    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    # Código duplicado
    serv_data = {"codigo": "P05-DUP", "nombre": "Servicio Base", "nivel1_id": setup_base_data["n1"].id}
    res_primero = client.post("/servicios/", json=serv_data, headers=headers)
    assert res_primero.status_code == 200

    res_dup = client.post("/servicios/", json=serv_data, headers=headers)
    assert res_dup.status_code == 400
    assert "duplicado" in res_dup.json()["detail"].lower()

    # Referencia inexistente (nivel1_id inválido)
    serv_invalido = {"codigo": "P05-INV", "nombre": "Servicio Huérfano", "nivel1_id": 999999}
    res_inv = client.post("/servicios/", json=serv_invalido, headers=headers)
    assert res_inv.status_code == 400
    assert "no existe" in res_inv.json()["detail"].lower()

def test_P06_importar_archivo_original(db_session):
    """P06: Importar archivo original (12 códigos N1 y 46 servicios N2)"""
    import_data()
    n1_excel_count = db_session.query(models.ServicioNivel1).filter(models.ServicioNivel1.codigo.like("SE.%")).count()
    n2_excel_count = db_session.query(models.ServicioNivel2).filter(models.ServicioNivel2.codigo.like("SE.%")).count()
    
    # 12 códigos del Excel
    assert n1_excel_count == 12
    # Exactamente 46 servicios físicos del catálogo Excel
    assert n2_excel_count == 46

def test_P07_repetir_importacion_idempotente(db_session):
    """P07: Repetir importación sin duplicar registros"""
    conteo_previo_n1 = db_session.query(models.ServicioNivel1).filter(models.ServicioNivel1.codigo.like("SE.%")).count()
    conteo_previo_n2 = db_session.query(models.ServicioNivel2).filter(models.ServicioNivel2.codigo.like("SE.%")).count()

    # Segunda corrida
    import_data()

    conteo_post_n1 = db_session.query(models.ServicioNivel1).filter(models.ServicioNivel1.codigo.like("SE.%")).count()
    conteo_post_n2 = db_session.query(models.ServicioNivel2).filter(models.ServicioNivel2.codigo.like("SE.%")).count()

    assert conteo_previo_n1 == 12
    assert conteo_post_n1 == 12
    assert conteo_previo_n2 == 46
    assert conteo_post_n2 == 46

def test_P08_revisar_SE12_y_atributos_ausentes(db_session):
    """P08: Revisar SE.12 y atributos ausentes"""
    # SE.12 unificado bajo nombre canónico
    se12 = db_session.query(models.ServicioNivel1).filter(models.ServicioNivel1.codigo == "SE.12").all()
    assert len(se12) == 1
    assert "Suministrar Analítica y Tableros de Control" in se12[0].nombre

    # Atributos ausentes conservados como nulos (no ceros ni inventados)
    servicios_incompletos = db_session.query(models.ServicioNivel2).filter(models.ServicioNivel2.codigo.in_(["SE.12.1", "SE.12.2", "SE.12.3"])).all()
    assert len(servicios_incompletos) == 3
    for s in servicios_incompletos:
        # Se confirma que campos vacíos en Excel quedaron en None
        assert s.metrica is None or s.metrica == ""
        assert s.minimo is None
        assert s.maximo is None
        assert s.clase_id is None
        assert s.criticidad_id is None
        assert s.tipo_id is None
        assert s.activo is None

def test_P09_crear_servicio_minimo_mayor_que_maximo(setup_base_data):
    """P09: Crear o editar servicio con mínimo mayor que máximo (Validación impide guardar)"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    payload = {
        "codigo": "P09-ERR",
        "nombre": "Servicio MinMax Erróneo",
        "nivel1_id": setup_base_data["n1"].id,
        "minimo": 500.0,
        "maximo": 100.0
    }
    res = client.post("/servicios/", json=payload, headers=headers)
    assert res.status_code == 422  # Validación Pydantic
    assert "menor o igual que el máximo" in res.text

def test_P10_buscar_y_filtrar_servicios(setup_base_data):
    """P10: Buscar y filtrar servicios con resultados coherentes"""
    token = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Búsqueda por texto
    res_search = client.get("/servicios/?q=SE.01", headers=headers)
    assert res_search.status_code == 200
    for s in res_search.json():
        assert "SE.01" in s["codigo"] or "SE.01" in s["nombre"]

    # Filtrar por estado activo 'S'
    res_activo = client.get("/servicios/?activo=S", headers=headers)
    assert res_activo.status_code == 200
    for s in res_activo.json():
        assert s["activo"] == "S"

def test_P11_asignar_responsable_seccion_distinta(db_session, setup_base_data):
    """P11: Asignar responsable de una sección distinta (operación rechazada)"""
    # Aislamiento de datos de prueba
    s_err = db_session.query(models.ServicioNivel2).filter(models.ServicioNivel2.codigo == "P11-ERR").first()
    if s_err:
        db_session.delete(s_err)
        db_session.commit()
    u_prev = db_session.query(models.Usuario).filter(models.Usuario.correo == "user_a@demo.com").first()
    if u_prev:
        db_session.delete(u_prev)
        db_session.commit()
    pst_prev = db_session.query(models.Puesto).filter(models.Puesto.codigo == "PST-A").first()
    if pst_prev:
        db_session.delete(pst_prev)
        db_session.commit()
    sec_a_prev = db_session.query(models.Seccion).filter(models.Seccion.codigo == "SEC-A").first()
    if sec_a_prev:
        db_session.delete(sec_a_prev)
        db_session.commit()
    sec_b_prev = db_session.query(models.Seccion).filter(models.Seccion.codigo == "SEC-B").first()
    if sec_b_prev:
        db_session.delete(sec_b_prev)
        db_session.commit()

    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    # Obtener departamento base existente (creado por create_admin.py o crear uno)
    depto = db_session.query(models.Departamento).first()
    if not depto:
        emp = models.Empresa(codigo="USAC-TEST", nombre="USAC Test", activo=True)
        db_session.add(emp)
        db_session.commit()
        area = models.Area(codigo="AREA-TEST", nombre="Area Test", empresa_id=emp.id, activo=True)
        db_session.add(area)
        db_session.commit()
        depto = models.Departamento(codigo="DEP-TEST", nombre="Depto Test", area_id=area.id, activo=True)
        db_session.add(depto)
        db_session.commit()

    sec_a = models.Seccion(codigo="SEC-A", nombre="Sección A", departamento_id=depto.id)
    sec_b = models.Seccion(codigo="SEC-B", nombre="Sección B", departamento_id=depto.id)
    db_session.add_all([sec_a, sec_b])
    db_session.commit()

    # Usuario pertenece al puesto de Sección A
    puesto_a = models.Puesto(codigo="PST-A", nombre="Puesto A", seccion_id=sec_a.id)
    db_session.add(puesto_a)
    db_session.commit()

    user_a = models.Usuario(
        nombre="Usuario Sec A",
        correo="user_a@demo.com",
        hashed_password=get_password_hash("clave"),
        rol="consulta",
        puesto_id=puesto_a.id
    )
    db_session.add(user_a)
    db_session.commit()

    # Intentar asignar el usuario de Sección A a un servicio asignado a Sección B
    payload = {
        "codigo": "P11-ERR",
        "nombre": "Servicio Conflicto",
        "nivel1_id": setup_base_data["n1"].id,
        "seccion_id": sec_b.id,
        "usuario_id": user_a.id
    }
    res = client.post("/servicios/", json=payload, headers=headers)
    assert res.status_code == 400
    assert "no pertenece a la sección" in res.json()["detail"].lower()

def test_P12_persistencia_sin_eliminar_volumenes(db_session):
    """P12: Reiniciar contenedores sin eliminar volúmenes (Persistencia de datos)"""
    # Simulamos cierre y reapertura de sesión de base de datos
    db_session.close()
    nueva_db = SessionLocal()
    
    # Comprobar que los datos previamente registrados persisten
    empresa = nueva_db.query(models.Empresa).filter(models.Empresa.codigo == "USAC").first()
    assert empresa is not None
    assert "Universidad de San Carlos" in empresa.nombre
    
    # Comprobar que los servicios persisten
    servicios = nueva_db.query(models.ServicioNivel2).filter(models.ServicioNivel2.codigo.like("SE.%")).count()
    assert servicios == 46
    nueva_db.close()
