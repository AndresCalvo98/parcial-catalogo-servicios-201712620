from pydantic import BaseModel, validator
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    password: str
    rol: str = "consulta"

class ServicioCreate(BaseModel):
    codigo: str
    nombre: str
    nivel1_id: int
    minimo: Optional[float] = None
    maximo: Optional[float] = None

    @validator("maximo")
    def check_min_max(cls, v, values):
        minimo = values.get("minimo")
        if minimo is not None and v is not None and minimo > v:
            raise ValueError("El mínimo debe ser menor o igual que el máximo (Regla P09)")
        return v
