from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Any
from datetime import datetime

# =========================================================================
# 1. AUTENTICACIÓN Y TOKENS (Conservado)
# =========================================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    rol: Optional[str] = "consulta"
    nombre: Optional[str] = None
    correo: Optional[str] = None
    usuario_id: Optional[int] = None

class TokenData(BaseModel):
    correo: Optional[str] = None
    rol: Optional[str] = None

# =========================================================================
# 2. ESTRUCTURA ORGANIZACIONAL (Conservado)
# =========================================================================

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

class UsuarioBase(BaseModel):
    nombre: str
    correo: str
    # Roles: administrador, consulta, solicitante, agente, aprobador
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
    puesto_nombre: Optional[str] = None
    seccion_nombre: Optional[str] = None
    departamento_nombre: Optional[str] = None
    area_nombre: Optional[str] = None
    empresa_nombre: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# =========================================================================
# 3. CATÁLOGO DE SERVICIOS (Conservado)
# =========================================================================

class CatalogoItemResponse(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)

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
    
    nivel1_nombre: Optional[str] = None
    clase_nombre: Optional[str] = None
    criticidad_nombre: Optional[str] = None
    tipo_nombre: Optional[str] = None
    seccion_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# =========================================================================
# 4. CMDB (CATEGORÍAS, CIs, RELACIONES Y GRAFOS)
# =========================================================================

class CategoriaCIBase(BaseModel):
    codigo: str
    nombre: str
    nivel: Optional[int] = 1
    parent_id: Optional[int] = None
    activo: Optional[bool] = True

class CategoriaCICreate(CategoriaCIBase):
    pass

class CategoriaCIResponse(CategoriaCIBase):
    id: int
    parent_nombre: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ConfigurationItemBase(BaseModel):
    codigo: str
    nombre: str
    tipo_ci: str # Hardware, Software, Red, Seguridad
    clasificacion_id: int
    descripcion: Optional[str] = None
    numero_serie: Optional[str] = None
    version: Optional[str] = None
    fecha_adquisicion: Optional[str] = None
    estado_actual: Optional[str] = "Activo"
    ubicacion_fisica: Optional[str] = None
    propietario_responsable: Optional[str] = None
    seccion_id: Optional[int] = None
    usuario_responsable_id: Optional[int] = None
    fecha_cambio: Optional[str] = None
    descripcion_cambio: Optional[str] = None
    documentacion_relacionada: Optional[str] = None
    enlaces_incidentes: Optional[str] = None
    niveles_seguridad: Optional[str] = "Medio"
    cumplimiento: Optional[str] = "Cumple"
    estado_configuracion: Optional[str] = "Aprobado"
    numero_licencia: Optional[str] = None
    fecha_vencimiento_licencia: Optional[str] = None
    direccion_ip: Optional[str] = None
    direccion_mac: Optional[str] = None
    sistema_operativo: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    cpu_cores: Optional[int] = None
    ram_gb: Optional[float] = None
    almacenamiento_gb: Optional[float] = None
    activo: Optional[bool] = True

class ConfigurationItemCreate(ConfigurationItemBase):
    pass

class ConfigurationItemUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo_ci: Optional[str] = None
    clasificacion_id: Optional[int] = None
    descripcion: Optional[str] = None
    numero_serie: Optional[str] = None
    version: Optional[str] = None
    fecha_adquisicion: Optional[str] = None
    estado_actual: Optional[str] = None
    ubicacion_fisica: Optional[str] = None
    propietario_responsable: Optional[str] = None
    seccion_id: Optional[int] = None
    usuario_responsable_id: Optional[int] = None
    niveles_seguridad: Optional[str] = None
    cumplimiento: Optional[str] = None
    estado_configuracion: Optional[str] = None
    numero_licencia: Optional[str] = None
    fecha_vencimiento_licencia: Optional[str] = None
    direccion_ip: Optional[str] = None
    direccion_mac: Optional[str] = None
    sistema_operativo: Optional[str] = None
    cpu_cores: Optional[int] = None
    ram_gb: Optional[float] = None
    almacenamiento_gb: Optional[float] = None
    activo: Optional[bool] = None

class ConfigurationItemResponse(ConfigurationItemBase):
    id: int
    categoria_nombre: Optional[str] = None
    categoria_codigo: Optional[str] = None
    seccion_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None
    servicios_count: Optional[int] = 0
    tickets_count: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)

class CIRelationshipCreate(BaseModel):
    ci_origen_id: int
    ci_destino_id: int
    tipo_relacion: str # depende_de, alojado_en, conectado_a
    descripcion: Optional[str] = None

class CIRelationshipResponse(BaseModel):
    id: int
    ci_origen_id: int
    ci_origen_codigo: Optional[str] = None
    ci_origen_nombre: Optional[str] = None
    ci_destino_id: int
    ci_destino_codigo: Optional[str] = None
    ci_destino_nombre: Optional[str] = None
    tipo_relacion: str
    descripcion: Optional[str] = None
    activo: bool
    model_config = ConfigDict(from_attributes=True)

class CIServicioCreate(BaseModel):
    ci_id: int
    servicio_nivel2_id: int
    criticidad_relacion: Optional[str] = "Alta"

class CIServicioResponse(BaseModel):
    id: int
    ci_id: int
    ci_codigo: Optional[str] = None
    ci_nombre: Optional[str] = None
    servicio_nivel2_id: int
    servicio_codigo: Optional[str] = None
    servicio_nombre: Optional[str] = None
    criticidad_relacion: str
    model_config = ConfigDict(from_attributes=True)

# =========================================================================
# 5. COLAS Y PERMISOS DE ATENCIÓN
# =========================================================================

class ColaBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    proceso: str # Uno de los 7 procesos ITIL
    nivel_soporte: Optional[int] = 1 # 0 a 4
    regla_ordenamiento: Optional[str] = "prioridad_antiguedad"
    sla_primera_atencion_min: Optional[int] = 60
    sla_resolucion_min: Optional[int] = 480
    activo: Optional[bool] = True

class ColaCreate(ColaBase):
    pass

class ColaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    nivel_soporte: Optional[int] = None
    regla_ordenamiento: Optional[str] = None
    sla_primera_atencion_min: Optional[int] = None
    sla_resolucion_min: Optional[int] = None
    activo: Optional[bool] = None

class ColaResponse(ColaBase):
    id: int
    tickets_activos_count: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)

class ColaMiembroCreate(BaseModel):
    cola_id: int
    usuario_id: Optional[int] = None
    rol: Optional[str] = None
    puede_consultar: Optional[bool] = True
    puede_atender: Optional[bool] = False
    puede_transferir: Optional[bool] = False
    puede_aprobar: Optional[bool] = False
    puede_administrar: Optional[bool] = False

class ColaMiembroResponse(BaseModel):
    id: int
    cola_id: int
    cola_codigo: Optional[str] = None
    cola_nombre: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario_nombre: Optional[str] = None
    rol: Optional[str] = None
    puede_consultar: bool
    puede_atender: bool
    puede_transferir: bool
    puede_aprobar: bool
    puede_administrar: bool
    activo: bool
    model_config = ConfigDict(from_attributes=True)

# =========================================================================
# 6. TICKETS, TRAZABILIDAD Y ACCIONES
# =========================================================================

class TicketCreate(BaseModel):
    titulo: str
    descripcion: str
    tipo_ticket: str # Solicitud de Acceso, Evento, Incidente, Solicitud de Cambio, Requisicion de Servicio, Problema
    proceso: str # Uno de los 7 procesos
    cola_id: int
    servicio_nivel2_id: int
    prioridad: Optional[str] = "Media"
    impacto: Optional[str] = "Medio"
    urgencia: Optional[str] = "Media"
    canal: Optional[str] = "Portal Web"
    
    # Justificación de CI
    sin_ci_justificado: Optional[bool] = False
    justificacion_sin_ci: Optional[str] = None
    ci_ids: Optional[List[int]] = [] # CIs asociados inicialmente

    # Campos específicos según proceso
    # Eventos
    categoria_evento: Optional[str] = None # E0, E1, E2, E3
    # Incidentes
    categoria_incidente: Optional[str] = None # I0 .. I6
    tipo_afectacion: Optional[str] = None # 'interrupcion', 'degradacion'
    redundancia_disponible: Optional[bool] = False
    duracion_estimada_horas: Optional[float] = None
    # Cambios
    evaluacion_impacto_riesgo: Optional[str] = None
    plan_pruebas: Optional[str] = None
    plan_reversion: Optional[str] = None
    fecha_planificada_ejecucion: Optional[str] = None
    # Accesos
    usuario_beneficiario_id: Optional[int] = None
    recurso_solicitado: Optional[str] = None
    permiso_requerido: Optional[str] = None
    tipo_accion_acceso: Optional[str] = "Provision"
    # Problemas
    causa_raiz: Optional[str] = None
    solucion_temporal: Optional[str] = None
    # Nuevos Servicios
    analisis_viabilidad: Optional[str] = None

class TicketUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    prioridad: Optional[str] = None
    impacto: Optional[str] = None
    urgencia: Optional[str] = None
    estado: Optional[str] = None
    responsable_id: Optional[int] = None
    cola_id: Optional[int] = None
    
    # Campos de resolución
    solucion_aplicada: Optional[str] = None
    duracion_real_horas: Optional[float] = None
    causa_raiz: Optional[str] = None
    solucion_definitiva: Optional[str] = None
    error_conocido: Optional[bool] = None

class TicketTransferirRequest(BaseModel):
    nueva_cola_id: int
    motivo: str

class TicketTransicionRequest(BaseModel):
    nuevo_estado: str
    motivo: Optional[str] = None
    solucion_aplicada: Optional[str] = None
    duracion_real_horas: Optional[float] = None
    servicio_catalogo_creado_id: Optional[int] = None

class TicketReaperturaRequest(BaseModel):
    motivo: str

class TicketComentarioCreate(BaseModel):
    mensaje: str
    es_nota_interna: Optional[bool] = False # True = sólo visible a agentes

class TicketComentarioResponse(BaseModel):
    id: int
    ticket_id: int
    autor_id: int
    autor_nombre: Optional[str] = None
    mensaje: str
    es_nota_interna: bool
    fecha_creacion: datetime
    model_config = ConfigDict(from_attributes=True)

class TicketAdjuntoResponse(BaseModel):
    id: int
    ticket_id: int
    nombre_archivo: str
    tamano_bytes: int
    mime_type: str
    subido_por_id: int
    subido_por_nombre: Optional[str] = None
    fecha_creacion: datetime
    model_config = ConfigDict(from_attributes=True)

class TicketAuditoriaResponse(BaseModel):
    id: int
    ticket_id: int
    actor_id: int
    actor_nombre: Optional[str] = None
    accion: str
    campo_modificado: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    motivo: Optional[str] = None
    fecha_creacion: datetime
    model_config = ConfigDict(from_attributes=True)

class TicketRelacionCreate(BaseModel):
    ticket_destino_id: int
    tipo_relacion: str # 'incidente_de_problema', 'cambio_de_problema', 'incidente_de_evento', 'relacionado_con'

class TicketResponse(BaseModel):
    id: int
    numero_ticket: str
    titulo: str
    descripcion: str
    tipo_ticket: str
    proceso: str
    canal: str
    estado: str
    prioridad: str
    impacto: str
    urgencia: str
    
    cola_id: int
    cola_nombre: Optional[str] = None
    servicio_nivel2_id: int
    servicio_nivel2_nombre: Optional[str] = None
    servicio_nivel2_codigo: Optional[str] = None
    servicio_nivel1_id: int
    servicio_nivel1_nombre: Optional[str] = None
    servicio_nivel1_codigo: Optional[str] = None
    
    solicitante_id: int
    solicitante_nombre: Optional[str] = None
    creador_id: int
    creador_nombre: Optional[str] = None
    responsable_id: Optional[int] = None
    responsable_nombre: Optional[str] = None

    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    fecha_primera_atencion: Optional[datetime] = None
    fecha_resolucion: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    fecha_reapertura: Optional[datetime] = None
    pausado: bool
    tiempo_pausado_minutos: int

    sin_ci_justificado: bool
    justificacion_sin_ci: Optional[str] = None

    # Específicos
    categoria_evento: Optional[str] = None
    evento_notificado: Optional[bool] = False
    categoria_incidente: Optional[str] = None
    tipo_afectacion: Optional[str] = None
    redundancia_disponible: Optional[bool] = False
    duracion_estimada_horas: Optional[float] = None
    duracion_real_horas: Optional[float] = None
    solucion_aplicada: Optional[str] = None
    
    evaluacion_impacto_riesgo: Optional[str] = None
    plan_pruebas: Optional[str] = None
    plan_reversion: Optional[str] = None
    aprobado_por_id: Optional[int] = None
    aprobado_por_nombre: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None

    usuario_beneficiario_id: Optional[int] = None
    usuario_beneficiario_nombre: Optional[str] = None
    recurso_solicitado: Optional[str] = None
    permiso_requerido: Optional[str] = None
    tipo_accion_acceso: Optional[str] = None

    causa_raiz: Optional[str] = None
    solucion_temporal: Optional[str] = None
    error_conocido: Optional[bool] = False
    solucion_definitiva: Optional[str] = None
    cambio_relacionado_id: Optional[int] = None

    analisis_viabilidad: Optional[str] = None
    servicio_catalogo_creado_id: Optional[int] = None

    # Resumen de listas
    cis_afectados_codigos: Optional[List[str]] = []
    total_comentarios: Optional[int] = 0
    total_adjuntos: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

# =========================================================================
# 7. FAQ / BASE DE CONOCIMIENTOS (NIVEL 0)
# =========================================================================

class ArticuloFAQBase(BaseModel):
    titulo: str
    categoria: str
    contenido: str
    palabras_clave: Optional[str] = None
    activo: Optional[bool] = True

class ArticuloFAQCreate(ArticuloFAQBase):
    pass

class ArticuloFAQResponse(ArticuloFAQBase):
    id: int
    vistas: int
    util_conteo: int
    model_config = ConfigDict(from_attributes=True)
