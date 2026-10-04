from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base

# === ESTRUCTURA ORGANIZACIONAL ===

class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    areas = relationship("Area", back_populates="empresa")

class Area(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    
    empresa = relationship("Empresa", back_populates="areas")
    departamentos = relationship("Departamento", back_populates="area")

class Departamento(Base):
    __tablename__ = "departamentos"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    area_id = Column(Integer, ForeignKey("areas.id"))
    
    area = relationship("Area", back_populates="departamentos")
    secciones = relationship("Seccion", back_populates="departamento")

class Seccion(Base):
    __tablename__ = "secciones"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    
    departamento = relationship("Departamento", back_populates="secciones")
    puestos = relationship("Puesto", back_populates="seccion")
    servicios_responsables = relationship("ServicioNivel2", back_populates="seccion_responsable")

class Puesto(Base):
    __tablename__ = "puestos"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    seccion_id = Column(Integer, ForeignKey("secciones.id"))
    
    seccion = relationship("Seccion", back_populates="puestos")
    usuarios = relationship("Usuario", back_populates="puesto")

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    rol = Column(String, default="consulta") # administrador o consulta
    activo = Column(Boolean, default=True)
    puesto_id = Column(Integer, ForeignKey("puestos.id"))
    
    puesto = relationship("Puesto", back_populates="usuarios")
    servicios_asignados = relationship("ServicioNivel2", back_populates="usuario_responsable")

# === CATÁLOGOS AUXILIARES ===

class ClaseServicio(Base):
    __tablename__ = "clases_servicio"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    servicios = relationship("ServicioNivel2", back_populates="clase_obj")

class Criticidad(Base):
    __tablename__ = "criticidades"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    servicios = relationship("ServicioNivel2", back_populates="criticidad_obj")

class TipoServicio(Base):
    __tablename__ = "tipos_servicio"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    servicios = relationship("ServicioNivel2", back_populates="tipo_obj")

# === CATÁLOGO DE SERVICIOS ===

class ServicioNivel1(Base):
    __tablename__ = "servicios_nivel1"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    
    servicios_nivel2 = relationship("ServicioNivel2", back_populates="servicio_nivel1")

class ServicioNivel2(Base):
    __tablename__ = "servicios_nivel2"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    activo = Column(String, nullable=True) # S, N o nulo (desconocido)
    descripcion = Column(String, nullable=True)
    metrica = Column(String, nullable=True)
    minimo = Column(Float, nullable=True)
    maximo = Column(Float, nullable=True)
    
    # Llaves foráneas
    nivel1_id = Column(Integer, ForeignKey("servicios_nivel1.id"))
    clase_id = Column(Integer, ForeignKey("clases_servicio.id"), nullable=True)
    criticidad_id = Column(Integer, ForeignKey("criticidades.id"), nullable=True)
    tipo_id = Column(Integer, ForeignKey("tipos_servicio.id"), nullable=True)
    
    # Responsables
    seccion_id = Column(Integer, ForeignKey("secciones.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    servicio_nivel1 = relationship("ServicioNivel1", back_populates="servicios_nivel2")
    clase_obj = relationship("ClaseServicio", back_populates="servicios")
    criticidad_obj = relationship("Criticidad", back_populates="servicios")
    tipo_obj = relationship("TipoServicio", back_populates="servicios")
    seccion_responsable = relationship("Seccion", back_populates="servicios_responsables")
    usuario_responsable = relationship("Usuario", back_populates="servicios_asignados")
