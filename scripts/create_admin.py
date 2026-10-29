import sys
import os
import random
from datetime import datetime, timedelta

# Asegurar acceso a los módulos en src/
for _p in [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from database import SessionLocal
import models
from auth import get_password_hash

def seed_demo_data():
    db = SessionLocal()
    print("=== CONFIGURANDO DATOS DE DEMOSTRACIÓN: SERVICE DESK, CMDB Y PROCESOS ITIL ===")
    
    try:
        # =====================================================================
        # 1. ESTRUCTURA ORGANIZACIONAL (Conservada del Parcial 2)
        # =====================================================================
        empresa = db.query(models.Empresa).filter(models.Empresa.codigo == "USAC").first()
        if not empresa:
            empresa = models.Empresa(codigo="USAC", nombre="Universidad de San Carlos de Guatemala", activo=True)
            db.add(empresa)
            db.commit()
            db.refresh(empresa)

        area = db.query(models.Area).filter(models.Area.codigo == "DTI", models.Area.empresa_id == empresa.id).first()
        if not area:
            area = models.Area(codigo="DTI", nombre="Dirección General de Tecnología", empresa_id=empresa.id, activo=True)
            db.add(area)
            db.commit()
            db.refresh(area)

        depto = db.query(models.Departamento).filter(models.Departamento.codigo == "DDEV", models.Departamento.area_id == area.id).first()
        if not depto:
            depto = models.Departamento(codigo="DDEV", nombre="Departamento de Desarrollo e Innovación", area_id=area.id, activo=True)
            db.add(depto)
            db.commit()
            db.refresh(depto)

        sec_bnd = db.query(models.Seccion).filter(models.Seccion.codigo == "SEC-BND", models.Seccion.departamento_id == depto.id).first()
        if not sec_bnd:
            sec_bnd = models.Seccion(codigo="SEC-BND", nombre="Sección de Arquitectura y Backend", departamento_id=depto.id, activo=True)
            db.add(sec_bnd)

        sec_ops = db.query(models.Seccion).filter(models.Seccion.codigo == "SEC-OPS", models.Seccion.departamento_id == depto.id).first()
        if not sec_ops:
            sec_ops = models.Seccion(codigo="SEC-OPS", nombre="Sección de Operaciones e Infraestructura", departamento_id=depto.id, activo=True)
            db.add(sec_ops)

        db.commit()
        db.refresh(sec_bnd)
        db.refresh(sec_ops)

        puesto_lead = db.query(models.Puesto).filter(models.Puesto.codigo == "PST-LEAD", models.Puesto.seccion_id == sec_bnd.id).first()
        if not puesto_lead:
            puesto_lead = models.Puesto(codigo="PST-LEAD", nombre="Líder Técnico de Software", seccion_id=sec_bnd.id, activo=True)
            db.add(puesto_lead)

        puesto_sop = db.query(models.Puesto).filter(models.Puesto.codigo == "PST-SOP", models.Puesto.seccion_id == sec_ops.id).first()
        if not puesto_sop:
            puesto_sop = models.Puesto(codigo="PST-SOP", nombre="Especialista de Monitoreo y Soporte", seccion_id=sec_ops.id, activo=True)
            db.add(puesto_sop)

        db.commit()
        db.refresh(puesto_lead)
        db.refresh(puesto_sop)

        # =====================================================================
        # 2. USUARIOS DE EVALUACIÓN (Sección 11: admin, solicitante, agentes, aprobador, consulta)
        # =====================================================================
        cuentas_info = [
            {"nombre": "Administrador General TI", "correo": "admin@demo.com", "pass": "admin123", "rol": "administrador", "puesto": puesto_lead.id},
            {"nombre": "Usuario Solicitante Institucional", "correo": "solicitante@demo.com", "pass": "clave123", "rol": "solicitante", "puesto": puesto_sop.id},
            {"nombre": "Agente de Soporte N1", "correo": "agente1@demo.com", "pass": "clave123", "rol": "agente", "puesto": puesto_sop.id},
            {"nombre": "Agente de Soporte N2", "correo": "agente2@demo.com", "pass": "clave123", "rol": "agente", "puesto": puesto_sop.id},
            {"nombre": "Comité de Aprobación CAB", "correo": "aprobador@demo.com", "pass": "clave123", "rol": "aprobador", "puesto": puesto_lead.id},
            {"nombre": "Operador de Consulta", "correo": "normal@demo.com", "pass": "clave", "rol": "consulta", "puesto": puesto_sop.id},
            {"nombre": "Usuario Inactivo Test", "correo": "inactivo@demo.com", "pass": "clave", "rol": "consulta", "puesto": puesto_sop.id, "activo": False}
        ]

        usuarios_dict = {}
        for c in cuentas_info:
            usr = db.query(models.Usuario).filter(models.Usuario.correo == c["correo"]).first()
            if not usr:
                usr = models.Usuario(
                    nombre=c["nombre"],
                    correo=c["correo"],
                    hashed_password=get_password_hash(c["pass"]),
                    rol=c["rol"],
                    puesto_id=c["puesto"],
                    activo=c.get("activo", True)
                )
                db.add(usr)
                db.commit()
                db.refresh(usr)
            else:
                usr.rol = c["rol"]
                usr.puesto_id = c["puesto"]
                usr.activo = c.get("activo", True)
                db.commit()
            usuarios_dict[c["correo"]] = usr

        print("Usuarios de evaluación configurados correctamente.")

        # =====================================================================
        # 3. COLAS FUNCIONALES (Exactamente una cola funcional por cada uno de los 7 procesos)
        # =====================================================================
        colas_config = [
            {
                "codigo": "COLA-NUEVOS-SERV",
                "nombre": "Cola de Nuevos Servicios TI",
                "descripcion": "Análisis, viabilidad e incorporación de servicios al catálogo.",
                "proceso": "Gestion de nuevos servicios",
                "nivel": 2,
                "regla": "prioridad_antiguedad",
                "sla_resp": 120,
                "sla_res": 2880
            },
            {
                "codigo": "COLA-CAMBIOS",
                "nombre": "Cola de Gestión de Cambios (RFC)",
                "descripcion": "Evaluación, planificación y autorización de cambios sobre infraestructura.",
                "proceso": "Gestion de cambios",
                "nivel": 3,
                "regla": "prioridad_antiguedad",
                "sla_resp": 60,
                "sla_res": 1440
            },
            {
                "codigo": "COLA-INCIDENTES",
                "nombre": "Cola de Gestión de Incidentes",
                "descripcion": "Atención, diagnóstico y restauración inmediata de servicios degradados o interrumpidos.",
                "proceso": "Gestion de incidentes",
                "nivel": 1,
                "regla": "prioridad_antiguedad",
                "sla_resp": 30,
                "sla_res": 240
            },
            {
                "codigo": "COLA-EVENTOS",
                "nombre": "Cola de Gestión de Eventos",
                "descripcion": "Monitoreo, registro E0-E3 y correlación con incidentes.",
                "proceso": "Gestion de eventos",
                "nivel": 1,
                "regla": "antiguedad",
                "sla_resp": 15,
                "sla_res": 120
            },
            {
                "codigo": "COLA-PROBLEMAS",
                "nombre": "Cola de Gestión de Problemas",
                "descripcion": "Investigación de causa raíz, soluciones temporales y errores conocidos.",
                "proceso": "Gestion de problemas",
                "nivel": 3,
                "regla": "prioridad_antiguedad",
                "sla_resp": 120,
                "sla_res": 4320
            },
            {
                "codigo": "COLA-ACCESOS",
                "nombre": "Cola de Gestión de Accesos",
                "descripcion": "Aprovisionamiento y revocación de permisos con aprobación previa.",
                "proceso": "Gestion de accesos",
                "nivel": 1,
                "regla": "prioridad_antiguedad",
                "sla_resp": 60,
                "sla_res": 480
            },
            {
                "codigo": "COLA-SERVICIOS-TI",
                "nombre": "Cola de Requisición de Servicios TI",
                "descripcion": "Cumplimiento de solicitudes estándar sobre servicios existentes en catálogo.",
                "proceso": "Gestion de servicios de tecnologia",
                "nivel": 1,
                "regla": "prioridad_antiguedad",
                "sla_resp": 45,
                "sla_res": 480
            }
        ]

        colas_dict = {}
        for ccfg in colas_config:
            cola = db.query(models.Cola).filter(models.Cola.codigo == ccfg["codigo"]).first()
            if not cola:
                cola = models.Cola(
                    codigo=ccfg["codigo"],
                    nombre=ccfg["nombre"],
                    descripcion=ccfg["descripcion"],
                    proceso=ccfg["proceso"],
                    nivel_soporte=ccfg["nivel"],
                    regla_ordenamiento=ccfg["regla"],
                    sla_primera_atencion_min=ccfg["sla_resp"],
                    sla_resolucion_min=ccfg["sla_res"],
                    activo=True
                )
                db.add(cola)
                db.commit()
                db.refresh(cola)
            colas_dict[ccfg["codigo"]] = cola

        print("7 Colas obligatorias configuradas exitosamente.")

        # =====================================================================
        # 4. MEMBRESÍA Y PERMISOS DE COLAS (Sección 5: roles y usuarios)
        # =====================================================================
        # Asignar agentes y aprobadores a colas
        for c_code, cola_obj in colas_dict.items():
            # Asignación al rol 'agente'
            m_rol_agente = db.query(models.ColaMiembro).filter(
                models.ColaMiembro.cola_id == cola_obj.id,
                models.ColaMiembro.rol == "agente"
            ).first()
            if not m_rol_agente:
                db.add(models.ColaMiembro(
                    cola_id=cola_obj.id,
                    rol="agente",
                    puede_consultar=True,
                    puede_atender=True,
                    puede_transferir=True,
                    puede_aprobar=False,
                    puede_administrar=False
                ))

            # Asignación al usuario agente1@demo.com específicamente
            m_u1 = db.query(models.ColaMiembro).filter(
                models.ColaMiembro.cola_id == cola_obj.id,
                models.ColaMiembro.usuario_id == usuarios_dict["agente1@demo.com"].id
            ).first()
            if not m_u1:
                db.add(models.ColaMiembro(
                    cola_id=cola_obj.id,
                    usuario_id=usuarios_dict["agente1@demo.com"].id,
                    puede_consultar=True,
                    puede_atender=True,
                    puede_transferir=True,
                    puede_aprobar=False,
                    puede_administrar=False
                ))

            # Asignación a agente2@demo.com
            m_u2 = db.query(models.ColaMiembro).filter(
                models.ColaMiembro.cola_id == cola_obj.id,
                models.ColaMiembro.usuario_id == usuarios_dict["agente2@demo.com"].id
            ).first()
            if not m_u2:
                db.add(models.ColaMiembro(
                    cola_id=cola_obj.id,
                    usuario_id=usuarios_dict["agente2@demo.com"].id,
                    puede_consultar=True,
                    puede_atender=True,
                    puede_transferir=True,
                    puede_aprobar=False,
                    puede_administrar=False
                ))

            # Asignación a aprobador en colas de Cambios, Nuevos Servicios y Accesos
            if cola_obj.proceso in ["Gestion de cambios", "Gestion de nuevos servicios", "Gestion de accesos"]:
                m_aprob = db.query(models.ColaMiembro).filter(
                    models.ColaMiembro.cola_id == cola_obj.id,
                    models.ColaMiembro.usuario_id == usuarios_dict["aprobador@demo.com"].id
                ).first()
                if not m_aprob:
                    db.add(models.ColaMiembro(
                        cola_id=cola_obj.id,
                        usuario_id=usuarios_dict["aprobador@demo.com"].id,
                        puede_consultar=True,
                        puede_atender=False,
                        puede_transferir=False,
                        puede_aprobar=True,
                        puede_administrar=False
                    ))

            # Asignación al usuario de consulta (sólo consultar, nunca atender/aprobar)
            m_cons = db.query(models.ColaMiembro).filter(
                models.ColaMiembro.cola_id == cola_obj.id,
                models.ColaMiembro.usuario_id == usuarios_dict["normal@demo.com"].id
            ).first()
            if not m_cons:
                db.add(models.ColaMiembro(
                    cola_id=cola_obj.id,
                    usuario_id=usuarios_dict["normal@demo.com"].id,
                    puede_consultar=True,
                    puede_atender=False,
                    puede_transferir=False,
                    puede_aprobar=False,
                    puede_administrar=False
                ))

        db.commit()
        print("Membresías y permisos de colas configurados.")

        # =====================================================================
        # 5. ASIGNACIONES DE SERVICIOS (Parcial 2: al menos 3 asignaciones válidas)
        # =====================================================================
        servicios_a_asignar = db.query(models.ServicioNivel2).limit(3).all()
        if len(servicios_a_asignar) >= 3:
            servicios_a_asignar[0].seccion_id = sec_bnd.id
            servicios_a_asignar[0].usuario_id = usuarios_dict["admin@demo.com"].id

            servicios_a_asignar[1].seccion_id = sec_bnd.id
            servicios_a_asignar[1].usuario_id = usuarios_dict["admin@demo.com"].id

            servicios_a_asignar[2].seccion_id = sec_ops.id
            servicios_a_asignar[2].usuario_id = usuarios_dict["normal@demo.com"].id
            db.commit()
            print("Tres asignaciones válidas vinculadas a servicios Nivel 2.")

        # =====================================================================
        # 6. ARTÍCULOS DE FAQ / BASE DE CONOCIMIENTOS (NIVEL 0 AUTOSERVICIO)
        # =====================================================================
        faq_items = [
            {
                "titulo": "¿Cómo restablecer mi contraseña institucional?",
                "categoria": "Contraseñas",
                "contenido": "Para restablecer su contraseña institucional, ingrese a la opción 'Restablecer Credenciales' en el portal USAC, ingrese su correo institucional y confirme el código de verificación SMS enviado a su número registrado.",
                "keywords": "password, contraseña, olvido, reset, credenciales"
            },
            {
                "titulo": "Configuración de la red Wi-Fi Eduroam USAC",
                "categoria": "Red / VPN",
                "contenido": "Seleccione la red 'eduroam', ingrese su usuario completo (usuario@usac.edu.gt) y su contraseña de dominio. En caso de solicitar certificado, seleccione 'No validar' o 'Usar certificados del sistema'.",
                "keywords": "wifi, eduroam, internet, red, inalámbrica"
            },
            {
                "titulo": "Conexión a la VPN Institucional para Teletrabajo",
                "categoria": "Red / VPN",
                "contenido": "Descargue el cliente FortiClient VPN desde el repositorio interno de software. Configure la pasarela remota vpn.usac.edu.gt en el puerto 10443 y active la autenticación de dos factores.",
                "keywords": "vpn, remoto, teletrabajo, forticlient, acceso"
            },
            {
                "titulo": "Solicitud de licencia de software institucional (Office 365)",
                "categoria": "Software",
                "contenido": "Todos los docentes y personal administrativo activo cuentan con licencia asignada de Office 365. Para activarla, inicie sesión en portal.office.com con sus credenciales institucionales.",
                "keywords": "office, word, excel, licencia, software, 365"
            },
            {
                "titulo": "Políticas y requisitos para solicitar acceso a bases de datos",
                "categoria": "Accesos",
                "contenido": "Las solicitudes de acceso a bases de datos productivas deben tramitarse mediante un ticket de 'Gestión de Accesos', indicando la justificación de negocio, y requieren aprobación formal de su jefe de sección.",
                "keywords": "acceso, base de datos, sql, permisos, aprobacion"
            }
        ]

        for fi in faq_items:
            art = db.query(models.ArticuloFAQ).filter(models.ArticuloFAQ.titulo == fi["titulo"]).first()
            if not art:
                db.add(models.ArticuloFAQ(
                    titulo=fi["titulo"],
                    categoria=fi["categoria"],
                    contenido=fi["contenido"],
                    palabras_clave=fi["keywords"],
                    vistas=15,
                    util_conteo=10,
                    activo=True
                ))
        db.commit()
        print("Base de conocimientos FAQ (Nivel 0) configurada.")

        # =====================================================================
        # 7. GENERACIÓN DE AL MENOS 35 TICKETS DE DEMOSTRACIÓN (5 por proceso)
        # =====================================================================
        existing_tickets_count = db.query(models.Ticket).count()
        if existing_tickets_count < 35:
            print("[INFO] Generando conjunto de demostración de al menos 35 tickets (5 por cada uno de los 7 procesos)...")
            
            s2_list = db.query(models.ServicioNivel2).limit(10).all()
            if not s2_list:
                print("[AVISO] No hay servicios Nivel 2 en base de datos. Asegúrese de ejecutar import_excel.py primero.")
                return

            u_sol = usuarios_dict["solicitante@demo.com"]
            u_ag1 = usuarios_dict["agente1@demo.com"]
            u_ag2 = usuarios_dict["agente2@demo.com"]
            u_apr = usuarios_dict["aprobador@demo.com"]
            u_adm = usuarios_dict["admin@demo.com"]

            # Obtener CIs para asociar
            ci_sample = db.query(models.ConfigurationItem).limit(10).all()

            tk_data = []

            # --- PROCESO 1: Gestión de nuevos servicios (5 tickets) ---
            c_ns = colas_dict["COLA-NUEVOS-SERV"]
            estados_ns = ["Solicitado", "En Análisis", "Aprobado", "En Implementación", "Cerrado"]
            for idx, est in enumerate(estados_ns):
                tk_data.append({
                    "num": f"TK-NS-{idx+1:03d}",
                    "titulo": f"Propuesta de nuevo servicio institucional #{idx+1}",
                    "desc": "Se solicita la incorporación de nueva plataforma de gestión de laboratorios virtuales.",
                    "tipo": "Requisicion de Servicio",
                    "proceso": "Gestion de nuevos servicios",
                    "cola": c_ns,
                    "estado": est,
                    "prioridad": "Media",
                    "solicitante": u_sol,
                    "creador": u_sol,
                    "responsable": u_ag1 if est != "Solicitado" else None,
                    "s2": s2_list[idx % len(s2_list)],
                    "sin_ci": True,
                    "just_sin_ci": "El servicio se encuentra en fase de diseño de concepto",
                    "analisis_viab": "Viabilidad técnica y financiera aprobada por dirección." if est in ["Aprobado", "En Implementación", "Cerrado"] else None
                })

            # --- PROCESO 2: Gestión de cambios (5 tickets) ---
            c_cm = colas_dict["COLA-CAMBIOS"]
            estados_cm = ["Solicitado", "En Evaluación de Riesgo", "Aprobado", "En Ejecución", "Cerrado"]
            for idx, est in enumerate(estados_cm):
                tk_data.append({
                    "num": f"TK-CHG-{idx+1:03d}",
                    "titulo": f"RFC: Actualización de infraestructura core #{idx+1}",
                    "desc": "Actualización de microcódigo y parches de seguridad en clúster de servidores de base de datos.",
                    "tipo": "Solicitud de Cambio",
                    "proceso": "Gestion de cambios",
                    "cola": c_cm,
                    "estado": est,
                    "prioridad": "Alta",
                    "solicitante": u_ag1,
                    "creador": u_ag1,
                    "responsable": u_ag2 if est != "Solicitado" else None,
                    "aprobador": u_apr if est in ["Aprobado", "En Ejecución", "Cerrado"] else None,
                    "fecha_aprob": datetime.utcnow() - timedelta(days=1) if est in ["Aprobado", "En Ejecución", "Cerrado"] else None,
                    "s2": s2_list[idx % len(s2_list)],
                    "eval_riesgo": "Riesgo medio de indisponibilidad temporal. Mitigado por ejecución en ventana de mantenimiento.",
                    "plan_pruebas": "Validación de conexión de sockets y consistencia de réplica tras reinicio.",
                    "plan_rev": "Restauración de snapshot previo en cabina SAN en caso de fallo crítico.",
                    "ci_afectado": ci_sample[idx % len(ci_sample)] if ci_sample else None
                })

            # --- PROCESO 3: Gestión de incidentes (7 tickets cubriendo I0 a I6) ---
            c_inc = colas_dict["COLA-INCIDENTES"]
            # Mapeo Diapositiva 16:
            # I0: No interrupción, Baja, Redundancia True
            # I1..I5: Duraciones crecientes, Media/Alta, Redundancia False
            # I6: Afecta seguridad, Alta, Redundancia False
            cat_inc_list = [
                ("I0", "No causa interrupción", "Baja", True, 0.5, "interrupcion"),
                ("I1", "Degradación en tiempo de respuesta de consultas", "Media", False, 2.5, "degradacion"),
                ("I2", "Caída de servicio secundario de reportes", "Media", False, 6.0, "interrupcion"),
                ("I3", "Fallo en nodo de procesamiento batch", "Alta", False, 24.0, "interrupcion"),
                ("I4", "Indisponibilidad de enlace WAN secundario", "Alta", False, 72.0, "interrupcion"),
                ("I5", "Fallo general en matriz de almacenamiento SAN", "Alta", False, 300.0, "interrupcion"),
                ("I6", "Alerta de acceso no autorizado y posible exfiltración", "Alta", False, 1.0, "interrupcion")
            ]
            for idx, (icat, itit, iprio, iredund, idur, itipo_af) in enumerate(cat_inc_list):
                tk_data.append({
                    "num": f"TK-INC-{idx+1:03d}",
                    "titulo": f"Incidente [{icat}]: {itit}",
                    "desc": f"Reporte de incidencia operativa clasificada como {icat} conforme a Diapositiva 16.",
                    "tipo": "Incidente",
                    "proceso": "Gestion de incidentes",
                    "cola": c_inc,
                    "estado": "Resuelto" if idx < 3 else ("En Atencion" if idx < 5 else "Abierto"),
                    "prioridad": iprio,
                    "solicitante": u_sol,
                    "creador": u_sol,
                    "responsable": u_ag1 if idx >= 2 else None,
                    "s2": s2_list[idx % len(s2_list)],
                    "cat_inc": icat,
                    "tipo_af": itipo_af,
                    "redundancia": iredund,
                    "dur_est": idur,
                    "sol_aplicada": "Reinicio de servicio y conmutación a nodo pasivo." if idx < 3 else None,
                    "ci_afectado": ci_sample[idx % len(ci_sample)] if ci_sample else None
                })

            # --- PROCESO 4: Gestión de eventos (5 tickets cubriendo E0 a E3) ---
            c_ev = colas_dict["COLA-EVENTOS"]
            cat_ev_list = [
                ("E0", "Evento programado: Respaldo nocturno completado", "Baja", False),
                ("E1", "Evento no programado sin impacto: Pico temporal de CPU 70%", "Baja", False),
                ("E2", "Evento con impacto: Pérdida de conectividad en puerto switch", "Media", True),
                ("E3", "Evento de seguridad: Múltiples intentos de inicio de sesión fallidos", "Alta", True),
                ("E0", "Evento programado: Sincronización de catálogos", "Baja", False)
            ]
            for idx, (ecat, etit, eprio, enotif) in enumerate(cat_ev_list):
                tk_data.append({
                    "num": f"TK-EVT-{idx+1:03d}",
                    "titulo": f"Evento [{ecat}]: {etit}",
                    "desc": f"Captura telemétrica clasificada bajo Diapositiva 15 como {ecat}.",
                    "tipo": "Evento",
                    "proceso": "Gestion de eventos",
                    "cola": c_ev,
                    "estado": "Cerrado" if not enotif else "En Atencion",
                    "prioridad": eprio,
                    "solicitante": u_adm,
                    "creador": u_adm,
                    "responsable": u_ag2 if enotif else None,
                    "s2": s2_list[idx % len(s2_list)],
                    "cat_evt": ecat,
                    "evt_notif": enotif,
                    "ci_afectado": ci_sample[idx % len(ci_sample)] if ci_sample else None
                })

            # --- PROCESO 5: Gestión de problemas (5 tickets) ---
            c_prb = colas_dict["COLA-PROBLEMAS"]
            estados_prb = ["Registrado", "En Diagnóstico", "Error Conocido", "Solución Definitiva", "Cerrado"]
            for idx, est in enumerate(estados_prb):
                tk_data.append({
                    "num": f"TK-PRB-{idx+1:03d}",
                    "titulo": f"Problema recurrente de conectividad en cluster #{idx+1}",
                    "desc": "Análisis de causa raíz ante incidentes recurrentes de caída de socket en servicios web.",
                    "tipo": "Problema",
                    "proceso": "Gestion de problemas",
                    "cola": c_prb,
                    "estado": est,
                    "prioridad": "Alta",
                    "solicitante": u_ag1,
                    "creador": u_ag1,
                    "responsable": u_ag2,
                    "s2": s2_list[idx % len(s2_list)],
                    "causa_raiz": "Fuga de memoria (memory leak) en versión antigua del middleware." if est in ["Error Conocido", "Solución Definitiva", "Cerrado"] else None,
                    "sol_temp": "Reinicio preventivo programado cada 48 horas mediante cron." if est in ["Error Conocido", "Solución Definitiva", "Cerrado"] else None,
                    "err_conocido": True if est in ["Error Conocido", "Solución Definitiva", "Cerrado"] else False,
                    "sol_def": "Actualización de compilación a versión corregida v2.4.1." if est in ["Solución Definitiva", "Cerrado"] else None,
                    "ci_afectado": ci_sample[idx % len(ci_sample)] if ci_sample else None
                })

            # --- PROCESO 6: Gestión de accesos (5 tickets) ---
            c_acc = colas_dict["COLA-ACCESOS"]
            estados_acc = ["Solicitado", "En Evaluación", "Aprobado", "Aprovisionado", "Cerrado"]
            for idx, est in enumerate(estados_acc):
                tk_data.append({
                    "num": f"TK-ACC-{idx+1:03d}",
                    "titulo": f"Solicitud de acceso a base de datos analítica #{idx+1}",
                    "desc": "El colaborador requiere permisos de sólo lectura sobre el esquema de registro académico.",
                    "tipo": "Solicitud de Acceso",
                    "proceso": "Gestion de accesos",
                    "cola": c_acc,
                    "estado": est,
                    "prioridad": "Media",
                    "solicitante": u_sol,
                    "creador": u_sol,
                    "responsable": u_ag1 if est != "Solicitado" else None,
                    "aprobador": u_apr if est in ["Aprobado", "Aprovisionado", "Cerrado"] else None,
                    "fecha_aprob": datetime.utcnow() - timedelta(days=2) if est in ["Aprobado", "Aprovisionado", "Cerrado"] else None,
                    "beneficiario": u_sol,
                    "recurso": "PostgreSQL catalogo_servicios_db / Schema Readonly",
                    "permiso": "SELECT ON tables",
                    "tipo_accion_acc": "Provision",
                    "s2": s2_list[idx % len(s2_list)],
                    "sin_ci": True,
                    "just_sin_ci": "Solicitud de permisos de software a nivel de credencial de usuario"
                })

            # --- PROCESO 7: Gestión de servicios de tecnología (5 tickets) ---
            c_st = colas_dict["COLA-SERVICIOS-TI"]
            estados_st = ["Solicitado", "En Atencion", "En Cumplimiento", "Resuelto", "Cerrado"]
            for idx, est in enumerate(estados_st):
                tk_data.append({
                    "num": f"TK-SRV-{idx+1:03d}",
                    "titulo": f"Requisición de servicio estándar #{idx+1}",
                    "desc": "Solicitud de aprovisionamiento de buzón de correo y configuración de firma institucional.",
                    "tipo": "Requisicion de Servicio",
                    "proceso": "Gestion de servicios de tecnologia",
                    "cola": c_st,
                    "estado": est,
                    "prioridad": "Baja",
                    "solicitante": u_sol,
                    "creador": u_sol,
                    "responsable": u_ag1 if est != "Solicitado" else None,
                    "s2": s2_list[idx % len(s2_list)],
                    "sin_ci": True,
                    "just_sin_ci": "Trámite administrativo de catálogo estándar"
                })

            # Insertar los tickets y sus relaciones
            for tk in tk_data:
                existing_tk = db.query(models.Ticket).filter(models.Ticket.numero_ticket == tk["num"]).first()
                if not existing_tk:
                    s2_obj = tk["s2"]
                    t_new = models.Ticket(
                        numero_ticket=tk["num"],
                        titulo=tk["titulo"],
                        descripcion=tk["desc"],
                        tipo_ticket=tk["tipo"],
                        proceso=tk["proceso"],
                        canal="Portal Web",
                        estado=tk["estado"],
                        prioridad=tk["prioridad"],
                        impacto="Medio",
                        urgencia="Media",
                        cola_id=tk["cola"].id,
                        servicio_nivel2_id=s2_obj.id,
                        servicio_nivel1_id=s2_obj.nivel1_id,
                        solicitante_id=tk["solicitante"].id,
                        creador_id=tk["creador"].id,
                        responsable_id=tk["responsable"].id if tk["responsable"] else None,
                        aprobado_por_id=tk["aprobador"].id if "aprobador" in tk and tk["aprobador"] else None,
                        fecha_aprobacion=tk.get("fecha_aprob"),
                        sin_ci_justificado=tk.get("sin_ci", False),
                        justificacion_sin_ci=tk.get("just_sin_ci"),
                        categoria_evento=tk.get("cat_evt"),
                        evento_notificado=tk.get("evt_notif", False),
                        categoria_incidente=tk.get("cat_inc"),
                        tipo_afectacion=tk.get("tipo_af"),
                        redundancia_disponible=tk.get("redundancia", False),
                        duracion_estimada_horas=tk.get("dur_est"),
                        solucion_aplicada=tk.get("sol_aplicada"),
                        evaluacion_impacto_riesgo=tk.get("eval_riesgo"),
                        plan_pruebas=tk.get("plan_pruebas"),
                        plan_reversion=tk.get("plan_rev"),
                        usuario_beneficiario_id=tk.get("beneficiario").id if tk.get("beneficiario") else None,
                        recurso_solicitado=tk.get("recurso"),
                        permiso_requerido=tk.get("permiso"),
                        tipo_accion_acceso=tk.get("tipo_accion_acc"),
                        causa_raiz=tk.get("causa_raiz"),
                        solucion_temporal=tk.get("sol_temp"),
                        error_conocido=tk.get("err_conocido", False),
                        solucion_definitiva=tk.get("sol_def"),
                        analisis_viabilidad=tk.get("analisis_viab"),
                        fecha_creacion=datetime.utcnow() - timedelta(days=random.randint(1, 10))
                    )
                    db.add(t_new)
                    db.commit()
                    db.refresh(t_new)

                    # Si tiene CI afectado, vincularlo
                    if "ci_afectado" in tk and tk["ci_afectado"]:
                        db.add(models.TicketCI(
                            ticket_id=t_new.id,
                            ci_id=tk["ci_afectado"].id,
                            rol_ci="Afectado"
                        ))

                    # Agregar comentario de apertura y auditoría
                    db.add(models.TicketComentario(
                        ticket_id=t_new.id,
                        autor_id=tk["solicitante"].id,
                        mensaje="Ticket creado formalmente en el sistema Service Desk.",
                        es_nota_interna=False
                    ))
                    db.add(models.TicketAuditoria(
                        ticket_id=t_new.id,
                        actor_id=tk["creador"].id,
                        accion="Creación",
                        campo_modificado="estado",
                        valor_anterior=None,
                        valor_nuevo=t_new.estado,
                        motivo="Inicialización de caso en cola de atención"
                    ))
                    db.commit()

            # Vincular ticket E2 o E3 a un Incidente (Requisito 7 & P11)
            evt_e2 = db.query(models.Ticket).filter(models.Ticket.categoria_evento == "E2").first()
            inc_target = db.query(models.Ticket).filter(models.Ticket.proceso == "Gestion de incidentes").first()
            if evt_e2 and inc_target:
                rel_exist = db.query(models.TicketRelacion).filter(
                    models.TicketRelacion.ticket_origen_id == evt_e2.id,
                    models.TicketRelacion.ticket_destino_id == inc_target.id
                ).first()
                if not rel_exist:
                    db.add(models.TicketRelacion(
                        ticket_origen_id=evt_e2.id,
                        ticket_destino_id=inc_target.id,
                        tipo_relacion="incidente_de_evento"
                    ))
                    db.commit()

            # Vincular Incidente a Problema y Problema a Cambio (Requisito P13)
            prb_target = db.query(models.Ticket).filter(models.Ticket.proceso == "Gestion de problemas").first()
            chg_target = db.query(models.Ticket).filter(models.Ticket.proceso == "Gestion de cambios").first()
            if inc_target and prb_target:
                rel_inc_prb = db.query(models.TicketRelacion).filter(
                    models.TicketRelacion.ticket_origen_id == inc_target.id,
                    models.TicketRelacion.ticket_destino_id == prb_target.id
                ).first()
                if not rel_inc_prb:
                    db.add(models.TicketRelacion(
                        ticket_origen_id=inc_target.id,
                        ticket_destino_id=prb_target.id,
                        tipo_relacion="incidente_de_problema"
                    ))
                    db.commit()

            if prb_target and chg_target:
                prb_target.cambio_relacionado_id = chg_target.id
                rel_prb_chg = db.query(models.TicketRelacion).filter(
                    models.TicketRelacion.ticket_origen_id == prb_target.id,
                    models.TicketRelacion.ticket_destino_id == chg_target.id
                ).first()
                if not rel_prb_chg:
                    db.add(models.TicketRelacion(
                        ticket_origen_id=prb_target.id,
                        ticket_destino_id=chg_target.id,
                        tipo_relacion="cambio_de_problema"
                    ))
                    db.commit()

            total_tks = db.query(models.Ticket).count()
            print(f"Demostración de tickets completada. Total de tickets en BD: {total_tks}")
        else:
            print(f"Tickets de demostración ya configurados ({existing_tickets_count} en BD).")

        print("\n*** INICIALIZACIÓN DE DEMOSTRACIÓN FINALIZADA CON ÉXITO ***")
        print("Cuentas disponibles para evaluación local:")
        print("  - Administrador: admin@demo.com       / admin123")
        print("  - Solicitante:   solicitante@demo.com / clave123")
        print("  - Agente N1:     agente1@demo.com     / clave123")
        print("  - Agente N2:     agente2@demo.com     / clave123")
        print("  - Aprobador:     aprobador@demo.com   / clave123")
        print("  - Consulta:      normal@demo.com      / clave\n")

    except Exception as e:
        print(f"[ERROR]: Fallo al sembrar datos de demo: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
