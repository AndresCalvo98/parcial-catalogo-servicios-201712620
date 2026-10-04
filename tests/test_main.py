import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import Usuario
from auth import get_password_hash

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def setup_users(db):
    inactivo = db.query(Usuario).filter(Usuario.correo == "inactivo@demo.com").first()
    if not inactivo:
        inactivo = Usuario(
            nombre="Usuario Inactivo",
            correo="inactivo@demo.com",
            hashed_password=get_password_hash("clave"),
            rol="consulta",
            activo=False
        )
        db.add(inactivo)

    normal = db.query(Usuario).filter(Usuario.correo == "normal@demo.com").first()
    if not normal:
        normal = Usuario(
            nombre="Usuario Normal",
            correo="normal@demo.com",
            hashed_password=get_password_hash("clave"),
            rol="consulta",
            activo=True
        )
        db.add(normal)
        
    db.commit()
    return {"admin": "admin@demo.com", "admin_pass": "admin123", 
            "inactivo": "inactivo@demo.com", "inactivo_pass": "clave",
            "normal": "normal@demo.com", "normal_pass": "clave"}

def get_token(correo, password):
    response = client.post("/token", data={"username": correo, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_login_invalid_credentials_P01():
    """Prueba P01: Credenciales invalidas"""
    response = client.post("/token", data={"username": "admin@demo.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "incorrectos" in response.json()["detail"]

def test_login_inactive_user_P02(setup_users):
    """Prueba P02: Usuario inactivo"""
    response = client.post("/token", data={"username": setup_users["inactivo"], "password": setup_users["inactivo_pass"]})
    assert response.status_code == 403
    assert "desactivado" in response.json()["detail"]

def test_create_service_unauthorized_P03(setup_users):
    """Prueba P03: Acceso denegado (requiere admin)"""
    token = get_token(setup_users["normal"], setup_users["normal_pass"])
    headers = {"Authorization": f"Bearer {token}"}
    data = {"codigo": "TEST-01", "nombre": "Test", "nivel1_id": 1}
    response = client.post("/servicios/", json=data, headers=headers)
    assert response.status_code == 403
    assert "administrador" in response.json()["detail"]

def test_create_service_duplicate_code_P05(setup_users):
    """Prueba P05: No permitir codigos de catalogo repetidos"""
    token = get_token(setup_users["admin"], setup_users["admin_pass"])
    headers = {"Authorization": f"Bearer {token}"}
    data = {"codigo": "TEST-DUP", "nombre": "Test Duplicado", "nivel1_id": 1}
    client.post("/servicios/", json=data, headers=headers)
    response = client.post("/servicios/", json=data, headers=headers)
    assert response.status_code == 400
    assert "duplicado" in response.json()["detail"]

def test_create_service_min_max_P09(setup_users):
    """Prueba P09: Minimo mayor que maximo"""
    token = get_token(setup_users["admin"], setup_users["admin_pass"])
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "codigo": "TEST-MINMAX",
        "nombre": "Test MinMax",
        "nivel1_id": 1,
        "minimo": 100,
        "maximo": 50
    }
    response = client.post("/servicios/", json=data, headers=headers)
    assert response.status_code == 422 
    assert "menor o igual que el" in response.text
