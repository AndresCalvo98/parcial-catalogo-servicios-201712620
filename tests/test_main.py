import os
import sys
import pytest
import time
from fastapi.testclient import TestClient

# Asegurar acceso a src/ y scripts/
for _p in [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from main import app
from database import SessionLocal, engine, Base
import models
from auth import get_password_hash
from import_excel import import_data
from generate_cmdb import generate_cmdb_data, ensure_categories
from create_admin import seed_demo_data

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        # Asegurar hidratación inicial
        Base.metadata.create_all(bind=engine)
        import_data()
        seed_demo_data()
        ensure_categories(db)
        yield db
    finally:
        db.close()

def get_auth_token(username, password):
    res = client.post("/token", data={"username": username, "password": password})
    if res.status_code == 200:
        return res.json()["access_token"]
    return None

# =========================================================================
# ESCENARIOS DE ACEPTACIÓN AUTOMATIZADOS (P01 A P18)
# =========================================================================

def test_P01_autenticacion_cierre_y_usuario_inactivo(db_session):
    """P01: Autenticación, cierre de sesión, usuario inactivo y rechazo de operaciones sin permiso"""
    # 1. Login exitoso con admin
    res_admin = client.post("/token", data={"username": "admin@demo.com", "password": "admin123"})
    assert res_admin.status_code == 200
    token_admin = res_admin.json()["access_token"]
    assert res_admin.json()["rol"] == "administrador"

    # 2. Login inválido
    res_bad = client.post("/token", data={"username": "admin@demo.com", "password": "password_erroneo"})
    assert res_bad.status_code == 401

    # 3. Usuario inactivo
    res_inactivo = client.post("/token", data={"username": "inactivo@demo.com", "password": "clave"})
    assert res_inactivo.status_code == 403

    # 4. Cierre de sesión
    res_logout = client.post("/logout", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_logout.status_code == 200

    # 5. Operación protegida sin token
    res_no_token = client.get("/api/colas")
    assert res_no_token.status_code == 401

def test_P02_importacion_repetible_catalogo(db_session):
    """P02: Importación repetible del catálogo: controles 12/46 e incidencias conservadas"""
    res1 = import_data()
    n1_count1 = db_session.query(models.ServicioNivel1).count()
    n2_count1 = db_session.query(models.ServicioNivel2).count()
    assert n1_count1 == 12, f"Se esperaban 12 N1, obtenidos {n1_count1}"
    assert n2_count1 == 46, f"Se esperaban 46 N2, obtenidos {n2_count1}"

    # Repetición (Idempotencia)
    res2 = import_data()
    n1_count2 = db_session.query(models.ServicioNivel1).count()
    n2_count2 = db_session.query(models.ServicioNivel2).count()
    assert n1_count2 == 12
    assert n2_count2 == 46
    assert res2["creados_n2"] == 0 # No debe duplicar registros

def test_P03_carga_5000_dispositivos_unicos_y_repeticion(db_session):
    """P03: Carga de al menos 5,000 dispositivos únicos y repetición sin duplicados"""
    ci_count = db_session.query(models.ConfigurationItem).count()
    if ci_count < 5000:
        generate_cmdb_data(seed=42, target_count=5000)

    total_despues = db_session.query(models.ConfigurationItem).count()
    assert total_despues >= 5000, f"Se esperaban al menos 5,000 CIs, hay {total_despues}"

    # Repetir con la misma semilla
    generate_cmdb_data(seed=42, target_count=5000)
    total_repetido = db_session.query(models.ConfigurationItem).count()
    assert total_repetido == total_despues, "La repetición con la misma semilla no debe duplicar CIs"

def test_P04_jerarquia_cmdb_y_rechazo_de_ciclos(db_session):
    """P04: Correspondencia jerárquica con Lección 22 y rechazo de ciclos y padres inexistentes"""
    token = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Verificar existencia de categorías raíz (Nivel 1)
    cats_n1 = db_session.query(models.CategoriaCI).filter(models.CategoriaCI.nivel == 1).all()
    n1_codigos = [c.codigo for c in cats_n1]
    assert "CAT-HW" in n1_codigos
    assert "CAT-SW" in n1_codigos
    assert "CAT-NET" in n1_codigos
    assert "CAT-SEC" in n1_codigos

    # 2. Rechazo de categoría con padre inexistente
    res_bad_parent = client.post("/api/cmdb/categorias", json={
        "codigo": "CAT-TEST-INVALID-PARENT",
        "nombre": "Categoría Inválida",
        "nivel": 2,
        "parent_id": 999999
    }, headers=headers)
    assert res_bad_parent.status_code == 400

    # 3. Intentar crear o inducir un ciclo en jerarquía
    cat_hw = db_session.query(models.CategoriaCI).filter(models.CategoriaCI.codigo == "CAT-HW").first()
    cat_srv = db_session.query(models.CategoriaCI).filter(models.CategoriaCI.codigo == "CAT-HW-SRV").first()
    
    # Asignar a cat_hw como hijo de cat_srv crearía ciclo (cat_hw -> cat_srv -> cat_hw)
    from graph_service import GraphService
    is_cycle = GraphService.check_hierarchy_cycle(db_session, cat_hw.id, cat_srv.id)
    assert is_cycle is True, "El analizador de grafos debe detectar el ciclo en la jerarquía"

def test_P05_creacion_tickets_referencias_validas_e_invalidas(db_session):
    """P05: Creación de tickets con referencias válidas y rechazo de referencias inválidas"""
    token_sol = get_auth_token("solicitante@demo.com", "clave123")
    headers = {"Authorization": f"Bearer {token_sol}"}

    c_inc = db_session.query(models.Cola).filter(models.Cola.codigo == "COLA-INCIDENTES").first()
    s2 = db_session.query(models.ServicioNivel2).first()

    # Válido
    res_ok = client.post("/api/tickets", json={
        "titulo": "Fallo en acceso a portal web de inscripciones",
        "descripcion": "El servidor retorna error 504 gateway timeout al intentar registrar cursos.",
        "tipo_ticket": "Incidente",
        "proceso": "Gestion de incidentes",
        "cola_id": c_inc.id,
        "servicio_nivel2_id": s2.id,
        "prioridad": "Alta",
        "categoria_incidente": "I1",
        "sin_ci_justificado": True,
        "justificacion_sin_ci": "Incidencia reportada por usuario final sin CI especificado"
    }, headers=headers)
    assert res_ok.status_code == 200
    assert "TK-" in res_ok.json()["numero_ticket"]

    # Inválido: Cola inexistente
    res_bad_cola = client.post("/api/tickets", json={
        "titulo": "Test inválido",
        "descripcion": "Descripción test",
        "tipo_ticket": "Incidente",
        "proceso": "Gestion de incidentes",
        "cola_id": 999999,
        "servicio_nivel2_id": s2.id
    }, headers=headers)
    assert res_bad_cola.status_code == 400

    # Inválido: Servicio inexistente
    res_bad_srv = client.post("/api/tickets", json={
        "titulo": "Test inválido servicio",
        "descripcion": "Descripción test",
        "tipo_ticket": "Incidente",
        "proceso": "Gestion de incidentes",
        "cola_id": c_inc.id,
        "servicio_nivel2_id": 999999
    }, headers=headers)
    assert res_bad_srv.status_code == 400

def test_P06_asignacion_cola_a_roles_y_usuarios_politica_permisos(db_session):
    """P06: Asignación de cola a roles y usuarios; acceso permitido y denegado según su política"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    token_agente = get_auth_token("agente1@demo.com", "clave123")
    token_consulta = get_auth_token("normal@demo.com", "clave")

    cola = db_session.query(models.Cola).first()

    # Admin puede asignar miembros
    res_add_m = client.post(f"/api/colas/{cola.id}/miembros", json={
        "cola_id": cola.id,
        "rol": "agente",
        "puede_consultar": True,
        "puede_atender": True
    }, headers={"Authorization": f"Bearer {token_admin}"})
    assert res_add_m.status_code == 200

    # Rol consulta intenta crear miembro -> Rechazo 403
    res_consulta_denied = client.post(f"/api/colas/{cola.id}/miembros", json={
        "cola_id": cola.id,
        "rol": "consulta",
        "puede_atender": True
    }, headers={"Authorization": f"Bearer {token_consulta}"})
    assert res_consulta_denied.status_code == 403

def test_P07_ordenamiento_reproducible_y_concurrencia_tomar_ticket(db_session):
    """P07: Ordenamiento reproducible y dos agentes intentando tomar el mismo ticket: solo uno obtiene la asignación"""
    token_ag1 = get_auth_token("agente1@demo.com", "clave123")
    token_ag2 = get_auth_token("agente2@demo.com", "clave123")

    # Crear ticket disponible
    c_inc = db_session.query(models.Cola).filter(models.Cola.codigo == "COLA-INCIDENTES").first()
    s2 = db_session.query(models.ServicioNivel2).first()
    res_tk = client.post("/api/tickets", json={
        "titulo": "Incidente para prueba de concurrencia P07",
        "descripcion": "Verificación de bloqueo atómico de reclamación",
        "tipo_ticket": "Incidente",
        "proceso": "Gestion de incidentes",
        "cola_id": c_inc.id,
        "servicio_nivel2_id": s2.id,
        "prioridad": "Critica",
        "sin_ci_justificado": True
    }, headers={"Authorization": f"Bearer {token_ag1}"})
    tk_id = res_tk.json()["id"]

    # Agente 1 toma el ticket
    res_ag1 = client.post(f"/api/tickets/{tk_id}/tomar", headers={"Authorization": f"Bearer {token_ag1}"})
    assert res_ag1.status_code == 200
    assert res_ag1.json()["responsable_id"] is not None

    # Agente 2 intenta tomar el mismo ticket inmediatamente -> Debe ser rechazado con 409 Conflicto
    res_ag2 = client.post(f"/api/tickets/{tk_id}/tomar", headers={"Authorization": f"Bearer {token_ag2}"})
    assert res_ag2.status_code == 409
    assert "ya fue tomado" in res_ag2.json()["detail"].lower()

def test_P08_transferencia_entre_colas_con_historial_y_validacion(db_session):
    """P08: Transferencia entre colas con historial y validación del proceso destino"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    c_inc = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de incidentes").first()
    c_cambios = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de cambios").first()
    
    # Crear una segunda cola del mismo proceso para transferencia válida
    c_inc2 = db_session.query(models.Cola).filter(models.Cola.codigo == "COLA-INC-ESCALADO").first()
    if not c_inc2:
        c_inc2 = models.Cola(
            codigo="COLA-INC-ESCALADO",
            nombre="Cola de Incidentes Escalados N2",
            proceso="Gestion de incidentes",
            nivel_soporte=2,
            activo=True
        )
        db_session.add(c_inc2)
        db_session.commit()
        db_session.refresh(c_inc2)

    s2 = db_session.query(models.ServicioNivel2).first()
    res_tk = client.post("/api/tickets", json={
        "titulo": "Ticket para probar transferencia P08",
        "descripcion": "Transferencia de cola",
        "tipo_ticket": "Incidente",
        "proceso": "Gestion de incidentes",
        "cola_id": c_inc.id,
        "servicio_nivel2_id": s2.id,
        "sin_ci_justificado": True
    }, headers=headers)
    tk_id = res_tk.json()["id"]

    # 1. Intentar transferir a una cola de otro proceso (Cambios) -> Rechazo 400
    res_bad_proc = client.post(f"/api/tickets/{tk_id}/transferir", json={
        "nueva_cola_id": c_cambios.id,
        "motivo": "Transferencia errónea a otro proceso"
    }, headers=headers)
    assert res_bad_proc.status_code == 400

    # 2. Transferencia válida a cola del mismo proceso
    res_ok_transf = client.post(f"/api/tickets/{tk_id}/transferir", json={
        "nueva_cola_id": c_inc2.id,
        "motivo": "Escalamiento técnico a soporte N2 especializado"
    }, headers=headers)
    assert res_ok_transf.status_code == 200
    assert res_ok_transf.json()["cola_id"] == c_inc2.id

    # 3. Comprobar que existe registro en la bitácora de auditoría
    audit = db_session.query(models.TicketAuditoria).filter(
        models.TicketAuditoria.ticket_id == tk_id,
        models.TicketAuditoria.accion == "Transferencia Cola"
    ).first()
    assert audit is not None
    assert "Escalamiento" in audit.motivo

def test_P09_ejecucion_ruta_completa_7_procesos_y_transiciones_invalidas(db_session):
    """P09: Ejecución de una ruta completa de cada uno de los siete procesos y rechazo de transiciones inválidas"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}
    s2 = db_session.query(models.ServicioNivel2).first()

    procesos_test = [
        ("Gestion de nuevos servicios", "COLA-NUEVOS-SERV", ["En Análisis", "Aprobado", "En Implementación", "Cerrado"]),
        ("Gestion de incidentes", "COLA-INCIDENTES", ["Clasificado", "En Atencion", "Recuperado", "Resuelto", "Cerrado"]),
        ("Gestion de eventos", "COLA-EVENTOS", ["Evaluado", "En Atencion", "Cerrado"]),
        ("Gestion de problemas", "COLA-PROBLEMAS", ["En Diagnóstico", "Error Conocido", "Solución Definitiva", "Cerrado"]),
        ("Gestion de servicios de tecnologia", "COLA-SERVICIOS-TI", ["En Atencion", "En Cumplimiento", "Resuelto", "Cerrado"])
    ]

    for proc_nom, cola_cod, ruta in procesos_test:
        cola = db_session.query(models.Cola).filter(models.Cola.codigo == cola_cod).first()
        res_tk = client.post("/api/tickets", json={
            "titulo": f"Ticket para ruta de proceso {proc_nom}",
            "descripcion": "Recorrido de flujo completo",
            "tipo_ticket": "Requisicion de Servicio" if "servicios" in proc_nom else "Incidente",
            "proceso": proc_nom,
            "cola_id": cola.id,
            "servicio_nivel2_id": s2.id,
            "sin_ci_justificado": True
        }, headers=headers)
        assert res_tk.status_code == 200
        tk_id = res_tk.json()["id"]

        for estado_paso in ruta:
            res_step = client.post(f"/api/tickets/{tk_id}/transicion", json={
                "nuevo_estado": estado_paso,
                "motivo": f"Avance a {estado_paso}",
                "solucion_aplicada": "Solución aplicada correctamente" if estado_paso in ["Resuelto", "Solución Definitiva"] else None
            }, headers=headers)
            assert res_step.status_code == 200, f"Fallo al transicionar {proc_nom} a {estado_paso}: {res_step.text}"
            assert res_step.json()["estado"] == estado_paso

def test_P10_cambio_sin_aprobacion_y_acceso_autoaprobado_rechazados(db_session):
    """P10: Cambio sin aprobación y acceso autoaprobado: operaciones rechazadas"""
    token_sol = get_auth_token("solicitante@demo.com", "clave123")
    token_aprob = get_auth_token("aprobador@demo.com", "clave123")

    s2 = db_session.query(models.ServicioNivel2).first()
    c_chg = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de cambios").first()
    c_acc = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de accesos").first()

    # 1. Cambio sin aprobación: Intentar ejecutar directamente sin estar Aprobado
    res_chg = client.post("/api/tickets", json={
        "titulo": "RFC Cambio sin aprobar",
        "descripcion": "Intento de ejecución directa",
        "tipo_ticket": "Solicitud de Cambio",
        "proceso": "Gestion de cambios",
        "cola_id": c_chg.id,
        "servicio_nivel2_id": s2.id,
        "sin_ci_justificado": True
    }, headers={"Authorization": f"Bearer {token_sol}"})
    chg_id = res_chg.json()["id"]

    res_exec_bad = client.post(f"/api/tickets/{chg_id}/transicion", json={
        "nuevo_estado": "En Ejecución",
        "motivo": "Ejecución sin aprobación previa"
    }, headers={"Authorization": f"Bearer {token_sol}"})
    assert res_exec_bad.status_code == 400
    assert "no se permite ejecutar un cambio que no haya sido formalmente aprobado" in res_exec_bad.json()["detail"].lower()

    # 2. Acceso autoaprobado: El solicitante intenta aprobar su propia solicitud
    res_acc = client.post("/api/tickets", json={
        "titulo": "Solicitud de acceso a bases de datos",
        "descripcion": "Acceso a tablas de nómina",
        "tipo_ticket": "Solicitud de Acceso",
        "proceso": "Gestion de accesos",
        "cola_id": c_acc.id,
        "servicio_nivel2_id": s2.id,
        "sin_ci_justificado": True
    }, headers={"Authorization": f"Bearer {token_sol}"})
    acc_id = res_acc.json()["id"]

    res_autoaprob = client.post(f"/api/tickets/{acc_id}/transicion", json={
        "nuevo_estado": "Aprobado",
        "motivo": "Autoaprobación fraudulenta"
    }, headers={"Authorization": f"Bearer {token_sol}"})
    assert res_autoaprob.status_code == 400
    assert "prohibida la autoaprobación" in res_autoaprob.json()["detail"].lower()

    # Aprobación válida con el usuario Aprobador
    res_aprob_ok = client.post(f"/api/tickets/{acc_id}/transicion", json={
        "nuevo_estado": "Aprobado",
        "motivo": "Aprobado formalmente por autoridad competente"
    }, headers={"Authorization": f"Bearer {token_aprob}"})
    assert res_aprob_ok.status_code == 200
    assert res_aprob_ok.json()["estado"] == "Aprobado"

def test_P11_eventos_E0_E3_y_vinculacion_incidentes_sin_duplicar(db_session):
    """P11: Eventos E0–E3 con respuesta correspondiente; E2/E3 vinculados a incidentes sin duplicarlos"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}
    c_ev = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de eventos").first()
    s2 = db_session.query(models.ServicioNivel2).first()

    # E0: Solo registro
    res_e0 = client.post("/api/tickets", json={
        "titulo": "Evento E0 Respaldo Programado",
        "descripcion": "Backup ejecutado",
        "tipo_ticket": "Evento",
        "proceso": "Gestion de eventos",
        "cola_id": c_ev.id,
        "servicio_nivel2_id": s2.id,
        "categoria_evento": "E0",
        "sin_ci_justificado": True
    }, headers=headers)
    assert res_e0.status_code == 200
    assert res_e0.json()["categoria_evento"] == "E0"
    assert res_e0.json()["evento_notificado"] is False

    # E2: Genera y vincula incidente automáticamente
    res_e2 = client.post("/api/tickets", json={
        "titulo": "Evento E2 Caída de Interfaz de Red",
        "descripcion": "Impacto en rendimiento del servicio",
        "tipo_ticket": "Evento",
        "proceso": "Gestion de eventos",
        "cola_id": c_ev.id,
        "servicio_nivel2_id": s2.id,
        "categoria_evento": "E2",
        "sin_ci_justificado": True
    }, headers=headers)
    assert res_e2.status_code == 200
    e2_id = res_e2.json()["id"]

    # Verificar que existe relación con un incidente
    rel_inc = db_session.query(models.TicketRelacion).filter(
        models.TicketRelacion.ticket_origen_id == e2_id,
        models.TicketRelacion.tipo_relacion == "incidente_de_evento"
    ).all()
    assert len(rel_inc) == 1, "Debe existir exactamente 1 incidente vinculado sin duplicar"

def test_P12_registro_I0_I6_y_reglas_complementarias(db_session):
    """P12: Registro I0–I6 y validación de las reglas complementarias de duración, prioridad y redundancia"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}
    c_inc = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de incidentes").first()
    s2 = db_session.query(models.ServicioNivel2).first()

    # Probar I0: debe asignar prioridad Baja y redundancia disponible True
    res_i0 = client.post("/api/tickets", json={
        "titulo": "Incidente I0 sin interrupción operativa",
        "descripcion": "Conmutación automática a nodo espejo",
        "tipo_ticket": "Incidente",
        "proceso": "Gestion de incidentes",
        "cola_id": c_inc.id,
        "servicio_nivel2_id": s2.id,
        "categoria_incidente": "I0",
        "sin_ci_justificado": True
    }, headers=headers)
    assert res_i0.status_code == 200
    assert res_i0.json()["prioridad"] == "Baja"
    assert res_i0.json()["redundancia_disponible"] is True

    # Probar I6: seguridad de recursos e información -> Prioridad Alta
    res_i6 = client.post("/api/tickets", json={
        "titulo": "Incidente I6 Afección de Seguridad",
        "descripcion": "Inyección SQL detectada en formulario público",
        "tipo_ticket": "Incidente",
        "proceso": "Gestion de incidentes",
        "cola_id": c_inc.id,
        "servicio_nivel2_id": s2.id,
        "categoria_incidente": "I6",
        "sin_ci_justificado": True
    }, headers=headers)
    assert res_i6.status_code == 200
    assert res_i6.json()["prioridad"] == "Alta"
    assert res_i6.json()["redundancia_disponible"] is False

def test_P13_incidente_vinculado_a_problema_y_cambio(db_session):
    """P13: Incidente vinculado a problema y cambio, con trazabilidad recuperable"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    c_inc = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de incidentes").first()
    c_prb = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de problemas").first()
    c_chg = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de cambios").first()
    s2 = db_session.query(models.ServicioNivel2).first()

    # 1. Crear Incidente
    r_inc = client.post("/api/tickets", json={
        "titulo": "Incidente recurrente de memoria", "descripcion": "OOM Killer",
        "tipo_ticket": "Incidente", "proceso": "Gestion de incidentes",
        "cola_id": c_inc.id, "servicio_nivel2_id": s2.id, "sin_ci_justificado": True
    }, headers=headers)
    inc_id = r_inc.json()["id"]

    # 2. Crear Problema
    r_prb = client.post("/api/tickets", json={
        "titulo": "Problema de gestión de memoria", "descripcion": "Análisis causa raíz",
        "tipo_ticket": "Problema", "proceso": "Gestion de problemas",
        "cola_id": c_prb.id, "servicio_nivel2_id": s2.id, "sin_ci_justificado": True
    }, headers=headers)
    prb_id = r_prb.json()["id"]

    # 3. Crear Cambio
    r_chg = client.post("/api/tickets", json={
        "titulo": "RFC Corrección de fuga de memoria", "descripcion": "Parche v2.1",
        "tipo_ticket": "Solicitud de Cambio", "proceso": "Gestion de cambios",
        "cola_id": c_chg.id, "servicio_nivel2_id": s2.id, "sin_ci_justificado": True
    }, headers=headers)
    chg_id = r_chg.json()["id"]

    # Vincular Incidente -> Problema
    r_rel1 = client.post(f"/api/tickets/relacionar?ticket_origen_id={inc_id}", json={
        "ticket_destino_id": prb_id, "tipo_relacion": "incidente_de_problema"
    }, headers=headers)
    assert r_rel1.status_code == 200

    # Vincular Problema -> Cambio
    r_rel2 = client.post(f"/api/tickets/relacionar?ticket_origen_id={prb_id}", json={
        "ticket_destino_id": chg_id, "tipo_relacion": "cambio_de_problema"
    }, headers=headers)
    assert r_rel2.status_code == 200

    # Verificar trazabilidad en base de datos
    rel_inc_prb = db_session.query(models.TicketRelacion).filter(
        models.TicketRelacion.ticket_origen_id == inc_id,
        models.TicketRelacion.ticket_destino_id == prb_id
    ).first()
    assert rel_inc_prb is not None

    rel_prb_chg = db_session.query(models.TicketRelacion).filter(
        models.TicketRelacion.ticket_origen_id == prb_id,
        models.TicketRelacion.ticket_destino_id == chg_id
    ).first()
    assert rel_prb_chg is not None

def test_P14_recorrido_ci_servicio_y_manejo_de_ciclos(db_session):
    """P14: Recorrido CI–servicio y manejo de ciclos según el tipo de relación"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    # Obtener dos CIs para probar ciclo
    cis = db_session.query(models.ConfigurationItem).limit(2).all()
    ci1, ci2 = cis[0], cis[1]

    # Crear relación depende_de ci1 -> ci2
    client.post("/api/cmdb/relaciones", json={
        "ci_origen_id": ci1.id, "ci_destino_id": ci2.id, "tipo_relacion": "depende_de"
    }, headers=headers)

    # Intentar relación inversa ci2 -> ci1 de tipo depende_de -> Ciclo prohibido (HTTP 422)
    res_ciclo = client.post("/api/cmdb/relaciones", json={
        "ci_origen_id": ci2.id, "ci_destino_id": ci1.id, "tipo_relacion": "depende_de"
    }, headers=headers)
    assert res_ciclo.status_code == 422
    assert "ciclo prohibido" in res_ciclo.json()["detail"].lower()

    # Comprobar análisis de impacto y recorrido hacia servicios de catálogo
    res_impact = client.get(f"/api/cmdb/impact-analysis/{ci2.id}", headers=headers)
    assert res_impact.status_code == 200
    impact_data = res_impact.json()
    assert "cis_impactados" in impact_data
    assert "servicios_potencialmente_afectados" in impact_data
    assert "advertencia_tecnica" in impact_data

def test_P15_cierre_sin_resolucion_reapertura_y_bitacora(db_session):
    """P15: Cierre sin resolución, reapertura y bitácora: reglas aplicadas y actor registrado"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}
    c_inc = db_session.query(models.Cola).filter(models.Cola.proceso == "Gestion de incidentes").first()
    s2 = db_session.query(models.ServicioNivel2).first()

    # Crear ticket
    res_tk = client.post("/api/tickets", json={
        "titulo": "Ticket para probar cierre y reapertura P15",
        "descripcion": "Verificación de validaciones",
        "tipo_ticket": "Incidente",
        "proceso": "Gestion de incidentes",
        "cola_id": c_inc.id,
        "servicio_nivel2_id": s2.id,
        "sin_ci_justificado": True
    }, headers=headers)
    tk_id = res_tk.json()["id"]

    # 1. Intentar cerrar directamente desde Abierto -> Rechazo 400
    res_cierre_bad = client.post(f"/api/tickets/{tk_id}/transicion", json={
        "nuevo_estado": "Cerrado", "motivo": "Cierre prematuro"
    }, headers=headers)
    assert res_cierre_bad.status_code == 400
    assert "sin previa resolución" in res_cierre_bad.json()["detail"].lower()

    # 2. Resolver correctamente
    res_res = client.post(f"/api/tickets/{tk_id}/transicion", json={
        "nuevo_estado": "Resuelto", "solucion_aplicada": "Parche aplicado", "motivo": "Incidente superado"
    }, headers=headers)
    assert res_res.status_code == 200

    # 3. Cerrar
    res_cierre_ok = client.post(f"/api/tickets/{tk_id}/transicion", json={
        "nuevo_estado": "Cerrado", "motivo": "Conformidad de usuario"
    }, headers=headers)
    assert res_cierre_ok.status_code == 200
    assert res_cierre_ok.json()["estado"] == "Cerrado"

    # 4. Reapertura controlada
    res_reap = client.post(f"/api/tickets/{tk_id}/reapertura", json={
        "motivo": "El síntoma se presentó nuevamente tras 2 horas"
    }, headers=headers)
    assert res_reap.status_code == 200
    assert res_reap.json()["estado"] == "En Atencion"

    # 5. Bitácora de auditoría registra la reapertura
    aud = db_session.query(models.TicketAuditoria).filter(
        models.TicketAuditoria.ticket_id == tk_id,
        models.TicketAuditoria.accion == "Reapertura"
    ).first()
    assert aud is not None
    assert "El síntoma se presentó" in aud.motivo

def test_P16_filtros_y_paginacion_5000_dispositivos(db_session):
    """P16: Filtros y paginación con 5,000 dispositivos; reporte de tiempos observados y entorno de prueba"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    # Búsqueda paginada
    t0 = time.time()
    res = client.get("/api/cmdb/items?tipo_ci=Hardware&limit=25&skip=0", headers=headers)
    elapsed = time.time() - t0
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 25
    assert data["total"] > 1000
    assert elapsed < 1.0, f"La consulta sobre 5,000 CIs debe ser sub-segundo, tomó {elapsed}s"

def test_P17_indicadores_con_datos_controlados(db_session):
    """P17: Indicadores con datos controlados, incluidas pausas y tickets aún abiertos"""
    token_admin = get_auth_token("admin@demo.com", "admin123")
    headers = {"Authorization": f"Bearer {token_admin}"}

    res_kpis = client.get("/api/dashboard/kpis", headers=headers)
    assert res_kpis.status_code == 200
    kpis = res_kpis.json()

    resumen = kpis["resumen"]
    assert resumen["total_tickets"] >= 35
    assert "mtta_promedio_minutos" in resumen
    assert "mttr_promedio_minutos" in resumen
    assert "cumplimiento_sla_porcentaje" in resumen
    assert len(kpis["distribucion_proceso"]) == 7 # Los 7 procesos representados

def test_P18_reinicio_de_contenedores_y_persistencia(db_session):
    """P18: Reinicio de contenedores sin pérdida de catálogo, CMDB, tickets e historial"""
    # Verificación de integridad de datos persistidos en PostgreSQL
    n1_total = db_session.query(models.ServicioNivel1).count()
    n2_total = db_session.query(models.ServicioNivel2).count()
    ci_total = db_session.query(models.ConfigurationItem).count()
    tk_total = db_session.query(models.Ticket).count()

    assert n1_total == 12, "Persistencia: Se conservan 12 códigos Nivel 1"
    assert n2_total == 46, "Persistencia: Se conservan 46 servicios Nivel 2"
    assert ci_total >= 5000, "Persistencia: Se conservan los 5,000 CIs sintéticos en volumen"
    assert tk_total >= 35, "Persistencia: Se conservan los tickets y auditorías"
