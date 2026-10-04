from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    rol: Optional[str] = "consulta"
    nombre: Optional[str] = None
    correo: Optional[str] = None

class TokenData(BaseModel):
    correo: Optional[str] = None
    rol: Optional[str] = None

# Organizacion: Empresa
class EmpresaBase(BaseModel):
    codigo: str
    nombre: str
    activo: Optional[bool] = True

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaUpdate(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None

class EmpresaResponse(EmpresaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Organizacion: Area
class AreaBase(BaseModel):
    codigo: str
    nombre: str
    empresa_id: int
    activo: Optional[bool] = True

class AreaCreate(AreaBase):
    pass

class AreaUpdate(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None

class AreaResponse(AreaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Organizacion: Departamento
class DepartamentoBase(BaseModel):
    codigo: str
    nombre: str
    area_id: int
    activo: Optional[bool] = True

class DepartamentoCreate(DepartamentoBase):
    pass

class DepartamentoUpdate(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None

class DepartamentoResponse(DepartamentoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Organizacion: Seccion
class SeccionBase(BaseModel):
    codigo: str
    nombre: str
    departamento_id: int
    activo: Optional[bool] = True

class SeccionCreate(SeccionBase):
    pass

class SeccionUpdate(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None

class SeccionResponse(SeccionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Organizacion: Puesto
class PuestoBase(BaseModel):
    codigo: str
    nombre: str
    seccion_id: int
    activo: Optional[bool] = True

class PuestoCreate(PuestoBase):
    pass

class PuestoUpdate(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None

class PuestoResponse(PuestoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Usuario
class UsuarioBase(BaseModel):
    nombre: str
    correo: str
    rol: Optional[str] = "consulta"
    puesto_id: Optional[int] = None
    activo: Optional[bool] = True

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    puesto_id: Optional[int] = None
    activo: Optional[bool] = None
    password: Optional[str] = None

class UsuarioResponse(UsuarioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Catalogos Auxiliares
class CatalogoItemResponse(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)

# Servicio Nivel 1
class ServicioN1Base(BaseModel):
    codigo: str
    nombre: str
    activo: Optional[bool] = True

class ServicioN1Create(ServicioN1Base):
    pass

class ServicioN1Update(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None

class ServicioN1Response(ServicioN1Base):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Servicio Nivel 2
class ServicioCreate(BaseModel):
    codigo: str
    nombre: str
    nivel1_id: int
    activo: Optional[str] = "S"
    descripcion: Optional[str] = None
    metrica: Optional[str] = None
    minimo: Optional[float] = None
    maximo: Optional[float] = None
    clase_id: Optional[int] = None
    criticidad_id: Optional[int] = None
    tipo_id: Optional[int] = None
    seccion_id: Optional[int] = None
    usuario_id: Optional[int] = None

    @model_validator(mode="after")
    def check_min_max(self):
        if self.minimo is not None and self.maximo is not None and self.minimo > self.maximo:
            raise ValueError("El mínimo debe ser menor o igual que el máximo (Regla P09)")
        return self

class ServicioUpdate(BaseModel):
    nombre: Optional[str] = None
    nivel1_id: Optional[int] = None
    activo: Optional[str] = None
    descripcion: Optional[str] = None
    metrica: Optional[str] = None
    minimo: Optional[float] = None
    maximo: Optional[float] = None
    clase_id: Optional[int] = None
    criticidad_id: Optional[int] = None
    tipo_id: Optional[int] = None
    seccion_id: Optional[int] = None
    usuario_id: Optional[int] = None

    @model_validator(mode="after")
    def check_min_max(self):
        if self.minimo is not None and self.maximo is not None and self.minimo > self.maximo:
            raise ValueError("El mínimo debe ser menor o igual que el máximo (Regla P09)")
        return self

class ServicioResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    activo: Optional[str] = None
    descripcion: Optional[str] = None
    metrica: Optional[str] = None
    minimo: Optional[float] = None
    maximo: Optional[float] = None
    nivel1_id: Optional[int] = None
    clase_id: Optional[int] = None
    criticidad_id: Optional[int] = None
    tipo_id: Optional[int] = None
    seccion_id: Optional[int] = None
    usuario_id: Optional[int] = None
    
    # Detalle de relaciones para ficha completa
    nivel1_nombre: Optional[str] = None
    clase_nombre: Optional[str] = None
    criticidad_nombre: Optional[str] = None
    tipo_nombre: Optional[str] = None
    seccion_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
