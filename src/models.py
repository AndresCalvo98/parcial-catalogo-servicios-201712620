from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from database import Base

# =========================================================================
# 1. ESTRUCTURA ORGANIZACIONAL (Conservada del Parcial 2)
# =========================================================================

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
    cis_responsables = relationship("ConfigurationItem", back_populates="seccion_responsable")

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
    # Roles soportados: administrador, consulta, solicitante, agente, aprobador
    rol = Column(String, default="consulta", index=True)
    activo = Column(Boolean, default=True)
    puesto_id = Column(Integer, ForeignKey("puestos.id"), nullable=True)
    
    puesto = relationship("Puesto", back_populates="usuarios")
    servicios_asignados = relationship("ServicioNivel2", back_populates="usuario_responsable")
    cis_asignados = relationship("ConfigurationItem", back_populates="usuario_responsable")
    colas_asignadas = relationship("ColaMiembro", back_populates="usuario")

# =========================================================================
# 2. CATÁLOGOS AUXILIARES (Conservados del Parcial 2)
# =========================================================================

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

# =========================================================================
# 3. CATÁLOGO DE SERVICIOS (Conservado del Parcial 2: 12 N1, 46 N2)
# =========================================================================

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
    activo = Column(String, nullable=True) # 'S', 'N' o NULL
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
    cis_vinculados = relationship("CIServicio", back_populates="servicio")

# =========================================================================
# 4. CMDB Y CLASIFICACIÓN JERÁRQUICA (Lección 22 & CMDB.xlsx)
# =========================================================================

class CategoriaCI(Base):
    """
    Clasificación jerárquica de CIs (Árbol estricto sin ciclos).
    Nivel 1: Dominio/Tipo (Hardware, Software, Red, Seguridad)
    Nivel 2: Subfamilia (Servidores, Almacenamiento, Sistemas Operativos, DBMS, etc.)
    Nivel 3: Clase específica de CI (Servidor Rack, BD Relacional, Firewall NGFW, etc.)
    """
    __tablename__ = "categorias_ci"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    nivel = Column(Integer, default=1, nullable=False)
    parent_id = Column(Integer, ForeignKey("categorias_ci.id"), nullable=True)
    activo = Column(Boolean, default=True)

    parent = relationship("CategoriaCI", remote_side=[id], backref=backref("subcategorias", lazy="joined"))
    dispositivos = relationship("ConfigurationItem", back_populates="categoria")

class ConfigurationItem(Base):
    """
    Elemento de Configuración (CI) / Dispositivo.
    Preserva los 20 campos de CMDB.xlsx y lección 22, más atributos técnicos.
    """
    __tablename__ = "configuration_items"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False) # Etiqueta única
    nombre = Column(String, index=True, nullable=False)
    tipo_ci = Column(String, index=True, nullable=False) # 'Hardware', 'Software', 'Red', 'Seguridad'
    clasificacion_id = Column(Integer, ForeignKey("categorias_ci.id"), nullable=False, index=True)
    
    # Atributos de CMDB.xlsx y Lección 22
    descripcion = Column(Text, nullable=True)
    numero_serie = Column(String, nullable=True, index=True)
    version = Column(String, nullable=True)
    fecha_adquisicion = Column(String, nullable=True)
    estado_actual = Column(String, default="Activo", index=True) # Activo, Inactivo, En Mantenimiento, Retirado
    ubicacion_fisica = Column(String, nullable=True, index=True) # Data Center USAC, Sala Servidores, etc.
    propietario_responsable = Column(String, nullable=True) # Nombre del equipo/área
    seccion_id = Column(Integer, ForeignKey("secciones.id"), nullable=True)
    usuario_responsable_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_cambio = Column(String, nullable=True)
    descripcion_cambio = Column(Text, nullable=True)
    documentacion_relacionada = Column(String, nullable=True)
    enlaces_incidentes = Column(String, nullable=True)
    niveles_seguridad = Column(String, default="Medio") # Bajo, Medio, Alto, Crítico
    cumplimiento = Column(String, default="Cumple") # Cumple, No Cumple, En Auditoría
    estado_configuracion = Column(String, default="Aprobado") # Aprobado, Pendiente, No Conforme
    numero_licencia = Column(String, nullable=True)
    fecha_vencimiento_licencia = Column(String, nullable=True)

    # Atributos técnicos complementarios (específicos por clase, IP opcional)
    direccion_ip = Column(String, nullable=True, index=True) # Opcional: solo si aplica
    direccion_mac = Column(String, nullable=True)
    sistema_operativo = Column(String, nullable=True)
    fabricante = Column(String, nullable=True)
    modelo = Column(String, nullable=True)
    cpu_cores = Column(Integer, nullable=True)
    ram_gb = Column(Float, nullable=True)
    almacenamiento_gb = Column(Float, nullable=True)
    activo = Column(Boolean, default=True) # Baja lógica

    # Relaciones
    categoria = relationship("CategoriaCI", back_populates="dispositivos")
    seccion_responsable = relationship("Seccion", back_populates="cis_responsables")
    usuario_responsable = relationship("Usuario", back_populates="cis_asignados")
    relaciones_salientes = relationship("CIRelationship", foreign_keys="[CIRelationship.ci_origen_id]", back_populates="ci_origen")
    relaciones_entrantes = relationship("CIRelationship", foreign_keys="[CIRelationship.ci_destino_id]", back_populates="ci_destino")
    servicios_asociados = relationship("CIServicio", back_populates="ci")
    tickets_asociados = relationship("TicketCI", back_populates="ci")

class CIRelationship(Base):
    """
    Relaciones técnicas entre CIs (Lección 22):
    - 'depende_de': Relación de dependencia directa (DAG obligatorio, ciclos prohibidos).
    - 'alojado_en': Hosting / Alojamiento (DAG obligatorio, ciclos prohibidos).
    - 'conectado_a': Enlace de red / topología física o lógica (permite ciclos / grafos mallados).
    """
    __tablename__ = "ci_relationships"
    id = Column(Integer, primary_key=True, index=True)
    ci_origen_id = Column(Integer, ForeignKey("configuration_items.id"), nullable=False, index=True)
    ci_destino_id = Column(Integer, ForeignKey("configuration_items.id"), nullable=False, index=True)
    tipo_relacion = Column(String, nullable=False, index=True) # 'depende_de', 'alojado_en', 'conectado_a'
    descripcion = Column(String, nullable=True)
    activo = Column(Boolean, default=True)

    ci_origen = relationship("ConfigurationItem", foreign_keys=[ci_origen_id], back_populates="relaciones_salientes")
    ci_destino = relationship("ConfigurationItem", foreign_keys=[ci_destino_id], back_populates="relaciones_entrantes")

class CIServicio(Base):
    """
    Vinculación entre Elementos de Configuración y Servicios de TI del Catálogo Nivel 2.
    Base fundamental para Graph Engineering y análisis de impacto de fallos sobre el catálogo.
    """
    __tablename__ = "ci_servicios"
    id = Column(Integer, primary_key=True, index=True)
    ci_id = Column(Integer, ForeignKey("configuration_items.id"), nullable=False, index=True)
    servicio_nivel2_id = Column(Integer, ForeignKey("servicios_nivel2.id"), nullable=False, index=True)
    criticidad_relacion = Column(String, default="Alta") # Alta, Media, Baja

    ci = relationship("ConfigurationItem", back_populates="servicios_asociados")
    servicio = relationship("ServicioNivel2", back_populates="cis_vinculados")

# =========================================================================
# 5. COLAS, ROLES Y ASIGNACIÓN (Service Desk ITIL)
# =========================================================================

class Cola(Base):
    """
    Colas de atención. Cada cola configura exactamente uno de los 7 procesos obligatorios.
    """
    __tablename__ = "colas"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False) # e.g. 'COLA-INCIDENTES'
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    proceso = Column(String, nullable=False, index=True) # Uno de los 7 procesos ITIL
    nivel_soporte = Column(Integer, default=1) # 0: Autoservicio, 1: Help Desk, 2: Soporte Técnico, 3: Ingenieros, 4: Externo
    regla_ordenamiento = Column(String, default="prioridad_antiguedad") # prioridad_antiguedad, antiguedad, sla_urgente
    sla_primera_atencion_min = Column(Integer, default=60) # Objetivo configurable primera respuesta
    sla_resolucion_min = Column(Integer, default=480) # Objetivo configurable resolución
    activo = Column(Boolean, default=True)

    miembros = relationship("ColaMiembro", back_populates="cola")
    tickets = relationship("Ticket", back_populates="cola")

class ColaMiembro(Base):
    """
    Asignación de cola a usuarios, roles o ambos, con permisos granulares:
    consultar, atender, transferir, aprobar, administrar.
    """
    __tablename__ = "cola_miembros"
    id = Column(Integer, primary_key=True, index=True)
    cola_id = Column(Integer, ForeignKey("colas.id"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    rol = Column(String, nullable=True, index=True) # 'agente', 'aprobador', 'administrador', etc.
    puede_consultar = Column(Boolean, default=True)
    puede_atender = Column(Boolean, default=False)
    puede_transferir = Column(Boolean, default=False)
    puede_aprobar = Column(Boolean, default=False)
    puede_administrar = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)

    cola = relationship("Cola", back_populates="miembros")
    usuario = relationship("Usuario", back_populates="colas_asignadas")

# =========================================================================
# 6. TICKETS Y TRAZABILIDAD (7 Procesos, Lección 25)
# =========================================================================

class Ticket(Base):
    """
    Entidad Central de Ticket para los 7 procesos ITIL obligatorios.
    Integra tipología de Diapositiva 14, clasificación de Eventos E0-E3 (Diapo 15)
    e Incidentes I0-I6 (Diapo 16), auditoría completa y control de concurrencia.
    """
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    numero_ticket = Column(String, unique=True, index=True, nullable=False) # e.g. 'TK-2026-00001'
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    
    # Clasificación principal
    tipo_ticket = Column(String, nullable=False, index=True) 
    # Tipos de Diapo 14: Solicitud de Acceso, Evento, Incidente, Solicitud de Cambio, Requisicion de Servicio, Problema
    proceso = Column(String, nullable=False, index=True)
    # 7 Procesos obligatorios:
    # 1. Gestion de nuevos servicios
    # 2. Gestion de cambios
    # 3. Gestion de incidentes
    # 4. Gestion de eventos
    # 5. Gestion de problemas
    # 6. Gestion de accesos
    # 7. Gestion de servicios de tecnologia
    
    canal = Column(String, default="Portal Web") # Portal Web, Email, Chat, Telefono, Monitoreo
    estado = Column(String, default="Abierto", index=True)
    # Estados generales: Abierto, Asignado, En Atencion, En Espera, Resuelto, Cerrado, Rechazado, Cancelado
    prioridad = Column(String, default="Media", index=True) # Baja, Media, Alta, Critica
    impacto = Column(String, default="Medio") # Bajo, Medio, Alto
    urgencia = Column(String, default="Media") # Baja, Media, Alta

    # Relaciones funcionales obligatorias
    cola_id = Column(Integer, ForeignKey("colas.id"), nullable=False, index=True)
    servicio_nivel2_id = Column(Integer, ForeignKey("servicios_nivel2.id"), nullable=False, index=True)
    servicio_nivel1_id = Column(Integer, ForeignKey("servicios_nivel1.id"), nullable=False, index=True)
    
    solicitante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    creador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    responsable_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)

    # Fechas y métricas de atención
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_primera_atencion = Column(DateTime, nullable=True)
    fecha_resolucion = Column(DateTime, nullable=True)
    fecha_cierre = Column(DateTime, nullable=True)
    fecha_reapertura = Column(DateTime, nullable=True)
    pausado = Column(Boolean, default=False)
    fecha_inicio_pausa = Column(DateTime, nullable=True)
    tiempo_pausado_minutos = Column(Integer, default=0)
    
    # Justificación de CI opcional
    sin_ci_justificado = Column(Boolean, default=False)
    justificacion_sin_ci = Column(Text, nullable=True)

    # === ATRIBUTOS ESPECÍFICOS POR PROCESO (LECCIÓN 25) ===

    # Gestión de Eventos (Diapositiva 15: E0, E1, E2, E3)
    categoria_evento = Column(String, nullable=True)
    evento_notificado = Column(Boolean, default=False)

    # Gestión de Incidentes (Diapositiva 16: I0 a I6)
    categoria_incidente = Column(String, nullable=True) # I0 .. I6
    tipo_afectacion = Column(String, nullable=True) # 'interrupcion', 'degradacion'
    redundancia_disponible = Column(Boolean, default=False)
    duracion_estimada_horas = Column(Float, nullable=True)
    duracion_real_horas = Column(Float, nullable=True)
    solucion_aplicada = Column(Text, nullable=True)

    # Gestión de Cambios (RFC)
    evaluacion_impacto_riesgo = Column(Text, nullable=True)
    plan_pruebas = Column(Text, nullable=True)
    plan_reversion = Column(Text, nullable=True)
    fecha_planificada_ejecucion = Column(String, nullable=True)
    aprobado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_aprobacion = Column(DateTime, nullable=True)

    # Gestión de Accesos
    usuario_beneficiario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    recurso_solicitado = Column(String, nullable=True)
    permiso_requerido = Column(String, nullable=True)
    tipo_accion_acceso = Column(String, nullable=True) # Provision, Revocacion

    # Gestión de Problemas
    causa_raiz = Column(Text, nullable=True)
    solucion_temporal = Column(Text, nullable=True)
    error_conocido = Column(Boolean, default=False)
    solucion_definitiva = Column(Text, nullable=True)
    cambio_relacionado_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)

    # Gestión de Nuevos Servicios
    analisis_viabilidad = Column(Text, nullable=True)
    servicio_catalogo_creado_id = Column(Integer, ForeignKey("servicios_nivel2.id"), nullable=True)

    # Relaciones ORM
    cola = relationship("Cola", back_populates="tickets")
    servicio_nivel2 = relationship("ServicioNivel2", foreign_keys=[servicio_nivel2_id])
    servicio_nivel1 = relationship("ServicioNivel1", foreign_keys=[servicio_nivel1_id])
    solicitante = relationship("Usuario", foreign_keys=[solicitante_id])
    creador = relationship("Usuario", foreign_keys=[creador_id])
    responsable = relationship("Usuario", foreign_keys=[responsable_id])
    aprobador = relationship("Usuario", foreign_keys=[aprobado_por_id])
    usuario_beneficiario = relationship("Usuario", foreign_keys=[usuario_beneficiario_id])
    
    cis_afectados = relationship("TicketCI", back_populates="ticket")
    relaciones_origen = relationship("TicketRelacion", foreign_keys="[TicketRelacion.ticket_origen_id]", back_populates="ticket_origen")
    relaciones_destino = relationship("TicketRelacion", foreign_keys="[TicketRelacion.ticket_destino_id]", back_populates="ticket_destino")
    comentarios = relationship("TicketComentario", back_populates="ticket", cascade="all, delete-orphan")
    adjuntos = relationship("TicketAdjunto", back_populates="ticket", cascade="all, delete-orphan")
    auditoria = relationship("TicketAuditoria", back_populates="ticket", cascade="all, delete-orphan")

class TicketCI(Base):
    """Asociación muchos a muchos entre Tickets y CIs afectados"""
    __tablename__ = "ticket_cis"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    ci_id = Column(Integer, ForeignKey("configuration_items.id"), nullable=False, index=True)
    rol_ci = Column(String, default="Afectado") # Afectado, Causa Raíz, Modificado

    ticket = relationship("Ticket", back_populates="cis_afectados")
    ci = relationship("ConfigurationItem", back_populates="tickets_asociados")

class TicketRelacion(Base):
    """Relaciones entre tickets (Incidente -> Problema, Problema -> Cambio, Evento -> Incidente, etc.)"""
    __tablename__ = "ticket_relaciones"
    id = Column(Integer, primary_key=True, index=True)
    ticket_origen_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    ticket_destino_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    tipo_relacion = Column(String, nullable=False, index=True) # 'incidente_de_problema', 'cambio_de_problema', 'incidente_de_evento', 'relacionado_con'

    ticket_origen = relationship("Ticket", foreign_keys=[ticket_origen_id], back_populates="relaciones_origen")
    ticket_destino = relationship("Ticket", foreign_keys=[ticket_destino_id], back_populates="relaciones_destino")

class TicketComentario(Base):
    """Comentarios de ticket: distingue notas internas (agentes) de mensajes públicos (solicitante)"""
    __tablename__ = "ticket_comentarios"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    autor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    mensaje = Column(Text, nullable=False)
    es_nota_interna = Column(Boolean, default=False, nullable=False) # True: sólo agentes/admin; False: visible al solicitante
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="comentarios")
    autor = relationship("Usuario")

class TicketAdjunto(Base):
    """Evidencias y archivos adjuntos con validación de tipo, tamaño y autorización de descarga"""
    __tablename__ = "ticket_adjuntos"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    nombre_archivo = Column(String, nullable=False)
    archivo_ruta = Column(String, nullable=False)
    tamano_bytes = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    subido_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="adjuntos")
    subido_por = relationship("Usuario")

class TicketAuditoria(Base):
    """Bitácora inmutable de auditoría: actor, fecha, valores anteriores y nuevos"""
    __tablename__ = "ticket_auditorias"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    accion = Column(String, nullable=False) # Creacion, Asignacion, Transicion, Transferencia, Edicion, Reapertura
    campo_modificado = Column(String, nullable=True)
    valor_anterior = Column(Text, nullable=True)
    valor_nuevo = Column(Text, nullable=True)
    motivo = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="auditoria")
    actor = relationship("Usuario")

# =========================================================================
# 7. BASE DE CONOCIMIENTOS / FAQ (Nivel 0 Autoservicio - Diapositiva 12)
# =========================================================================

class ArticuloFAQ(Base):
    """Artículos de conocimiento y preguntas frecuentes para el portal de autoservicio"""
    __tablename__ = "articulos_faq"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False, index=True)
    categoria = Column(String, nullable=False, index=True) # Contraseñas, Redes, Software, Hardware, Accesos
    contenido = Column(Text, nullable=False)
    palabras_clave = Column(String, nullable=True)
    vistas = Column(Integer, default=0)
    util_conteo = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
