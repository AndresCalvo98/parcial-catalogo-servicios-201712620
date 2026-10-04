from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import models, schemas, auth
from database import get_db
from jose import jwt, JWTError

app = FastAPI(title="API Catálogo de Servicios TI", description="Implementación para el parcial")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- DEPENDENCIAS DE SEGURIDAD ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Credenciales inválidas")
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.Usuario).filter(models.Usuario.correo == correo).first()
    if user is None or not user.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo o no encontrado (P02)")
    return user

def admin_required(current_user: models.Usuario = Depends(get_current_user)):
    if current_user.rol != "administrador":
        raise HTTPException(status_code=403, detail="Permisos insuficientes. Requiere rol administrador (P03).")
    return current_user

# --- ENDPOINTS ---

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.correo == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos (P01)")
    if not user.activo:
        raise HTTPException(status_code=403, detail="El usuario está desactivado (P02)")
    
    access_token = auth.create_access_token(data={"sub": user.correo, "rol": user.rol})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/servicios/")
def read_servicios(q: str = None, skip: int = 0, limit: int = 10, current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(models.ServicioNivel2)
    if q:
        query = query.filter(models.ServicioNivel2.nombre.ilike(f"%{q}%") | models.ServicioNivel2.codigo.ilike(f"%{q}%"))
    return query.offset(skip).limit(limit).all()

@app.post("/servicios/")
def create_servicio(servicio: schemas.ServicioCreate, current_user: models.Usuario = Depends(admin_required), db: Session = Depends(get_db)):
    db_serv = db.query(models.ServicioNivel2).filter(models.ServicioNivel2.codigo == servicio.codigo).first()
    if db_serv:
        raise HTTPException(status_code=400, detail="Código duplicado (P05)")
    
    nuevo = models.ServicioNivel2(**servicio.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo
