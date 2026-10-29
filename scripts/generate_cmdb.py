import sys
import os
import argparse
import random
from datetime import datetime, timedelta

# Asegurar acceso a src/ y scripts/
for _p in [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from database import SessionLocal, engine, Base
import models
from graph_service import GraphService

def ensure_categories(db):
    """Crea la taxonomía jerárquica de la CMDB en 3 niveles estrictos"""
    taxonomia = [
        # Nivel 1: Dominios / Tipos
        {"codigo": "CAT-HW", "nombre": "Infraestructura de Hardware", "nivel": 1, "parent": None},
        {"codigo": "CAT-SW", "nombre": "Software y Aplicaciones", "nivel": 1, "parent": None},
        {"codigo": "CAT-NET", "nombre": "Redes y Telecomunicaciones", "nivel": 1, "parent": None},
        {"codigo": "CAT-SEC", "nombre": "Seguridad y Ciberseguridad", "nivel": 1, "parent": None},

        # Nivel 2: Subfamilias
        {"codigo": "CAT-HW-SRV", "nombre": "Servidores y Cómputo", "nivel": 2, "parent": "CAT-HW"},
        {"codigo": "CAT-HW-STO", "nombre": "Sistemas de Almacenamiento", "nivel": 2, "parent": "CAT-HW"},
        {"codigo": "CAT-HW-WRK", "nombre": "Estaciones de Trabajo y Laptops", "nivel": 2, "parent": "CAT-HW"},
        {"codigo": "CAT-SW-SYS", "nombre": "Sistemas Operativos y Virtualización", "nivel": 2, "parent": "CAT-SW"},
        {"codigo": "CAT-SW-DB", "nombre": "Motores de Bases de Datos", "nivel": 2, "parent": "CAT-SW"},
        {"codigo": "CAT-SW-APP", "nombre": "Aplicaciones y Middleware", "nivel": 2, "parent": "CAT-SW"},
        {"codigo": "CAT-NET-RUT", "nombre": "Enrutamiento y Conmutación", "nivel": 2, "parent": "CAT-NET"},
        {"codigo": "CAT-NET-WIFI", "nombre": "Redes Inalámbricas y Acceso", "nivel": 2, "parent": "CAT-NET"},
        {"codigo": "CAT-SEC-FW", "nombre": "Cortafuegos y Perímetro", "nivel": 2, "parent": "CAT-SEC"},
        {"codigo": "CAT-SEC-EDR", "nombre": "Protección de Endpoints y Auditoría", "nivel": 2, "parent": "CAT-SEC"},

        # Nivel 3: Clases Específicas de CI
        {"codigo": "CAT-HW-SRV-RCK", "nombre": "Servidor Rack / Blade", "nivel": 3, "parent": "CAT-HW-SRV"},
        {"codigo": "CAT-HW-SRV-TOW", "nombre": "Servidor Torre", "nivel": 3, "parent": "CAT-HW-SRV"},
        {"codigo": "CAT-HW-STO-SAN", "nombre": "Cabina de Discos SAN Tier 1", "nivel": 3, "parent": "CAT-HW-STO"},
        {"codigo": "CAT-HW-STO-NAS", "nombre": "Arreglo NAS Departamental", "nivel": 3, "parent": "CAT-HW-STO"},
        {"codigo": "CAT-HW-WRK-PC", "nombre": "Computadora Desktop Corporativa", "nivel": 3, "parent": "CAT-HW-WRK"},
        {"codigo": "CAT-HW-WRK-LAP", "nombre": "Laptop Corporativa de Gestión", "nivel": 3, "parent": "CAT-HW-WRK"},
        {"codigo": "CAT-SW-SYS-LIN", "nombre": "Sistema Operativo Linux Enterprise", "nivel": 3, "parent": "CAT-SW-SYS"},
        {"codigo": "CAT-SW-SYS-WIN", "nombre": "Sistema Operativo Windows Server", "nivel": 3, "parent": "CAT-SW-SYS"},
        {"codigo": "CAT-SW-SYS-HYP", "nombre": "Hipervisor de Virtualización", "nivel": 3, "parent": "CAT-SW-SYS"},
        {"codigo": "CAT-SW-DB-REL", "nombre": "Base de Datos Relacional SQL", "nivel": 3, "parent": "CAT-SW-DB"},
        {"codigo": "CAT-SW-DB-NOSQL", "nombre": "Base de Datos NoSQL Distribuida", "nivel": 3, "parent": "CAT-SW-DB"},
        {"codigo": "CAT-SW-APP-WEB", "nombre": "Servidor Web / API Gateway", "nivel": 3, "parent": "CAT-SW-APP"},
        {"codigo": "CAT-SW-APP-ERP", "nombre": "Sistema Core ERP / Académico", "nivel": 3, "parent": "CAT-SW-APP"},
        {"codigo": "CAT-NET-RUT-COR", "nombre": "Enrutador Core de Red BGP", "nivel": 3, "parent": "CAT-NET-RUT"},
        {"codigo": "CAT-NET-SWT-DIS", "nombre": "Switch de Distribución L2/L3", "nivel": 3, "parent": "CAT-NET-RUT"},
        {"codigo": "CAT-NET-WIFI-AP", "nombre": "Punto de Acceso Wi-Fi 6", "nivel": 3, "parent": "CAT-NET-WIFI"},
        {"codigo": "CAT-SEC-FW-NG", "nombre": "Next-Gen Firewall de Borde", "nivel": 3, "parent": "CAT-SEC-FW"},
        {"codigo": "CAT-SEC-EDR-AG", "nombre": "Agente EDR de Seguridad", "nivel": 3, "parent": "CAT-SEC-EDR"}
    ]

    cat_map = {}
    for item in taxonomia:
        cat = db.query(models.CategoriaCI).filter(models.CategoriaCI.codigo == item["codigo"]).first()
        parent_id = cat_map[item["parent"]] if item["parent"] else None
        if not cat:
            cat = models.CategoriaCI(
                codigo=item["codigo"],
                nombre=item["nombre"],
                nivel=item["nivel"],
                parent_id=parent_id,
                activo=True
            )
            db.add(cat)
            db.commit()
            db.refresh(cat)
        cat_map[item["codigo"]] = cat.id

    return cat_map

def generate_cmdb_data(seed: int = 42, target_count: int = 5000, clean: bool = False):
    """
    Generador determinista e idempotente de al menos 5,000 CIs sintéticos en PostgreSQL.
    Preserva fidelidad estricta a CMDB.xlsx y Lección 22.
    """
    db = SessionLocal()
    print(f"\n=======================================================")
    print(f" GENERADOR SINTÉTICO DE CMDB (Semilla: {seed}, Meta: {target_count})")
    print(f"=======================================================\n")

    try:
        # Asegurar tablas creadas
        Base.metadata.create_all(bind=engine)
        rng = random.Random(seed)

        if clean:
            print("[INFO] Limpieza explícita de CIs solicitada (--clean)...")
            db.query(models.CIServicio).delete()
            db.query(models.CIRelationship).delete()
            db.query(models.TicketCI).delete()
            db.query(models.ConfigurationItem).delete()
            db.commit()
            print("[INFO] Tablas de CMDB limpias.")

        cat_map = ensure_categories(db)
        
        # Obtener secciones, usuarios y servicios N2 de referencia
        secciones = db.query(models.Seccion).all()
        usuarios = db.query(models.Usuario).all()
        servicios_n2 = db.query(models.ServicioNivel2).all()

        sec_ids = [s.id for s in secciones] if secciones else [None]
        usr_ids = [u.id for u in usuarios] if usuarios else [None]

        ubicaciones = [
            "Data Center USAC - Rack 01", "Data Center USAC - Rack 02", "Data Center USAC - Rack 03",
            "Data Center USAC - Sala de Energía", "Sala Servidores DTI - Piso 2", "Sala Servidores DTI - Piso 3",
            "Edificio T-3 - Laboratorio 101", "Edificio T-3 - Laboratorio 102", "Edificio T-3 - Site de Comunicaciones",
            "Edificio Recursos Educativos - Nivel 2", "Oficinas Administrativas Rectoría", "Edificio DIGI - Sala Técnica"
        ]

        estados_ci = ["Activo", "Activo", "Activo", "Activo", "En Mantenimiento", "Inactivo", "Retirado"]
        niveles_sec = ["Bajo", "Medio", "Alto", "Crítico"]
        estados_cfg = ["Aprobado", "Aprobado", "Aprobado", "Pendiente", "No Conforme"]

        # Pool de plantillas por tipo
        pool_specs = [
            # Hardware - Servidores Rack
            {
                "tipo_ci": "Hardware", "cat_code": "CAT-HW-SRV-RCK", "prefix": "SRV-RCK",
                "fabricantes": ["Dell PowerEdge", "HPE ProLiant", "Lenovo ThinkSystem", "Cisco UCS"],
                "has_ip": True, "base_desc": "Servidor de cómputo para aplicaciones críticas",
                "cpu_opts": [16, 32, 64, 128], "ram_opts": [64.0, 128.0, 256.0, 512.0], "disk_opts": [1000.0, 2000.0, 4000.0],
                "os_opts": ["Red Hat Enterprise Linux 9", "Ubuntu Server 22.04 LTS", "Windows Server 2022 Datacenter"]
            },
            # Hardware - Storage SAN/NAS
            {
                "tipo_ci": "Hardware", "cat_code": "CAT-HW-STO-SAN", "prefix": "STO-SAN",
                "fabricantes": ["NetApp AFF", "Dell PowerStore", "Pure Storage FlashArray", "IBM FlashSystem"],
                "has_ip": True, "base_desc": "Cabina de almacenamiento masivo y alta redundancia",
                "cpu_opts": [8, 16], "ram_opts": [32.0, 64.0], "disk_opts": [10000.0, 20000.0, 50000.0],
                "os_opts": ["ONTAP OS", "PowerStoreOS", "Purity//FA", "IBM Storage Virtualize"]
            },
            # Hardware - Laptops y PCs
            {
                "tipo_ci": "Hardware", "cat_code": "CAT-HW-WRK-LAP", "prefix": "WRK-LAP",
                "fabricantes": ["Lenovo ThinkPad T14", "Dell Latitude 5420", "HP EliteBook 840"],
                "has_ip": True, "base_desc": "Equipo portátil corporativo de personal técnico",
                "cpu_opts": [4, 8], "ram_opts": [16.0, 32.0], "disk_opts": [512.0, 1000.0],
                "os_opts": ["Windows 11 Pro", "Ubuntu Desktop 24.04 LTS", "macOS Sonoma"]
            },
            # Software - Motores de Base de Datos
            {
                "tipo_ci": "Software", "cat_code": "CAT-SW-DB-REL", "prefix": "DBMS-SQL",
                "fabricantes": ["PostgreSQL Global Dev", "Oracle Corporation", "Microsoft SQL Server", "MySQL Community"],
                "has_ip": False, "base_desc": "Instancia de motor de base de datos relacional transaccional",
                "cpu_opts": [None], "ram_opts": [None], "disk_opts": [None],
                "os_opts": [None]
            },
            # Software - Aplicaciones Web y ERP
            {
                "tipo_ci": "Software", "cat_code": "CAT-SW-APP-ERP", "prefix": "APP-CORE",
                "fabricantes": ["DTI USAC Interno", "Odoo Enterprise", "Moodle LMS USAC", "Koha Library System"],
                "has_ip": False, "base_desc": "Módulo de aplicación de servicio institucional",
                "cpu_opts": [None], "ram_opts": [None], "disk_opts": [None],
                "os_opts": [None]
            },
            # Redes - Routers y Switches
            {
                "tipo_ci": "Red", "cat_code": "CAT-NET-SWT-DIS", "prefix": "NET-SWT",
                "fabricantes": ["Cisco Catalyst 9300", "Aruba CX 6300", "Juniper EX3400", "MikroTik Cloud Router"],
                "has_ip": True, "base_desc": "Conmutador de capa 2/3 con soporte PoE y VLANs",
                "cpu_opts": [2, 4], "ram_opts": [4.0, 8.0], "disk_opts": [16.0],
                "os_opts": ["Cisco IOS-XE", "ArubaOS-CX", "Junos OS", "RouterOS"]
            },
            # Seguridad - Firewalls
            {
                "tipo_ci": "Seguridad", "cat_code": "CAT-SEC-FW-NG", "prefix": "SEC-FW",
                "fabricantes": ["Fortinet FortiGate 200F", "Palo Alto PA-850", "Check Point Quantum Spark", "Sophos XGS"],
                "has_ip": True, "base_desc": "Dispositivo de seguridad perimetral, inspección TLS y VPN",
                "cpu_opts": [8, 16], "ram_opts": [16.0, 32.0], "disk_opts": [240.0],
                "os_opts": ["FortiOS 7.4", "PAN-OS 11.0", "Gaia R81.20", "Sophos Firewall OS"]
            }
        ]

        print(f"[PASO 1] Insertando / Actualizando {target_count} Dispositivos Sintéticos...")
        
        # Mapear CIs existentes para idempotencia
        existing_cis = {c.codigo: c.id for c in db.query(models.ConfigurationItem.codigo, models.ConfigurationItem.id).all()}
        
        created_count = 0
        updated_count = 0
        all_ci_ids = []

        batch = []
        counts_by_cat = {}

        for i in range(1, target_count + 1):
            tpl = pool_specs[i % len(pool_specs)]
            codigo = f"CI-{tpl['prefix']}-{i:05d}"
            nombre = f"{tpl['fabricantes'][i % len(tpl['fabricantes'])]} #{i}"
            clasificacion_id = cat_map[tpl["cat_code"]]

            # Contadores
            counts_by_cat[tpl["cat_code"]] = counts_by_cat.get(tpl["cat_code"], 0) + 1

            ip = f"10.{(i // 254) % 250}.{(i % 254) + 1}" if tpl["has_ip"] else None
            mac = f"52:54:00:{(i >> 16) & 0xff:02x}:{(i >> 8) & 0xff:02x}:{i & 0xff:02x}" if tpl["has_ip"] else None
            serie = f"SN-{rng.randint(100000, 999999)}-{i:05d}"
            version = f"v{rng.randint(1, 15)}.{rng.randint(0, 9)}"
            f_adq = f"202{rng.randint(1, 5)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
            ubic = rng.choice(ubicaciones)
            sec_id = rng.choice(sec_ids) if sec_ids else None
            usr_id = rng.choice(usr_ids) if usr_ids else None
            cpu = rng.choice(tpl["cpu_opts"])
            ram = rng.choice(tpl["ram_opts"])
            disk = rng.choice(tpl["disk_opts"])
            so = rng.choice(tpl["os_opts"])

            lic_num = f"LIC-USAC-{i:05d}" if tpl["tipo_ci"] == "Software" else None
            lic_venc = f"202{rng.randint(6, 9)}-12-31" if tpl["tipo_ci"] == "Software" else None

            if codigo in existing_cis:
                updated_count += 1
                all_ci_ids.append(existing_cis[codigo])
            else:
                ci_obj = models.ConfigurationItem(
                    codigo=codigo,
                    nombre=nombre,
                    tipo_ci=tpl["tipo_ci"],
                    clasificacion_id=clasificacion_id,
                    descripcion=f"{tpl['base_desc']} asignado a infraestructura USAC.",
                    numero_serie=serie,
                    version=version,
                    fecha_adquisicion=f_adq,
                    estado_actual=rng.choice(estados_ci),
                    ubicacion_fisica=ubic,
                    propietario_responsable="Dirección General de Tecnología (DTI)",
                    seccion_id=sec_id,
                    usuario_responsable_id=usr_id,
                    niveles_seguridad=rng.choice(niveles_sec),
                    cumplimiento="Cumple",
                    estado_configuracion=rng.choice(estados_cfg),
                    numero_licencia=lic_num,
                    fecha_vencimiento_licencia=lic_venc,
                    direccion_ip=ip,
                    direccion_mac=mac,
                    sistema_operativo=so,
                    fabricante=tpl["fabricantes"][0].split()[0],
                    modelo=tpl["fabricantes"][0],
                    cpu_cores=cpu,
                    ram_gb=ram,
                    almacenamiento_gb=disk,
                    activo=True
                )
                batch.append(ci_obj)
                created_count += 1

            if len(batch) >= 1000:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []

        if batch:
            db.bulk_save_objects(batch)
            db.commit()

        # Recargar IDs completos
        all_ci_records = db.query(models.ConfigurationItem.id, models.ConfigurationItem.tipo_ci).all()
        ci_ids_all = [c[0] for c in all_ci_records]
        hw_ids = [c[0] for c in all_ci_records if c[1] == "Hardware"]
        sw_ids = [c[0] for c in all_ci_records if c[1] == "Software"]
        net_ids = [c[0] for c in all_ci_records if c[1] == "Red"]
        sec_ids = [c[0] for c in all_ci_records if c[1] == "Seguridad"]

        print(f"[PASO 1 COMPLETADO] Dispositivos creados: {created_count}, actualizados/preservados: {updated_count}. Total en BD: {len(ci_ids_all)}")

        # [PASO 2] Generar Relaciones Técnicas Acíclicas (depende_de, alojado_en, conectado_a)
        print("[PASO 2] Verificando / Generando relaciones técnicas entre CIs...")
        existing_rels_count = db.query(models.CIRelationship).count()
        if existing_rels_count < 2500 and hw_ids and sw_ids and net_ids:
            new_rels = []
            # Software alojado en Hardware (DAG: SW -> HW)
            for idx, sw_id in enumerate(sw_ids[:1500]):
                hw_target = hw_ids[idx % len(hw_ids)]
                new_rels.append(models.CIRelationship(
                    ci_origen_id=sw_id,
                    ci_destino_id=hw_target,
                    tipo_relacion="alojado_en",
                    descripcion="Aplicación desplegada y ejecutándose en host físico"
                ))

            # Hardware conectado a Red (HW -> NET)
            for idx, hw_id in enumerate(hw_ids[:1500]):
                net_target = net_ids[idx % len(net_ids)]
                new_rels.append(models.CIRelationship(
                    ci_origen_id=hw_id,
                    ci_destino_id=net_target,
                    tipo_relacion="conectado_a",
                    descripcion="Conexión de interfaz de red física a switch"
                ))

            # Aplicaciones dependen de BD (SW -> SW) - Siempre de índice menor a mayor para asegurar aciclicidad
            for idx in range(min(500, len(sw_ids) - 1)):
                if idx % 2 == 0:
                    new_rels.append(models.CIRelationship(
                        ci_origen_id=sw_ids[idx + 1],
                        ci_destino_id=sw_ids[idx],
                        tipo_relacion="depende_de",
                        descripcion="Dependencia de persistencia hacia motor de base de datos"
                    ))

            db.bulk_save_objects(new_rels)
            db.commit()
            print(f"[PASO 2 COMPLETADO] {len(new_rels)} relaciones técnicas generadas exitosamente.")
        else:
            print(f"[PASO 2] Relaciones técnicas ya existentes ({existing_rels_count}).")

        # [PASO 3] Vinculación de CIs a los 46 Servicios de TI de Nivel 2
        print("[PASO 3] Verificando vínculos entre CIs y Servicios Nivel 2...")
        existing_ci_serv_count = db.query(models.CIServicio).count()
        if existing_ci_serv_count < 200 and servicios_n2 and ci_ids_all:
            ci_servicios = []
            for s_idx, s2 in enumerate(servicios_n2):
                # Vincular entre 3 y 8 CIs a cada servicio N2
                for k in range(5):
                    target_ci = ci_ids_all[(s_idx * 7 + k) % len(ci_ids_all)]
                    ci_servicios.append(models.CIServicio(
                        ci_id=target_ci,
                        servicio_nivel2_id=s2.id,
                        criticidad_relacion="Alta" if k == 0 else "Media"
                    ))
            db.bulk_save_objects(ci_servicios)
            db.commit()
            print(f"[PASO 3 COMPLETADO] {len(ci_servicios)} vínculos CI-Servicio generados.")
        else:
            print(f"[PASO 3] Vínculos CI-Servicio ya existentes ({existing_ci_serv_count}).")

        # Reporte de Cantidades por Nivel y Categoría (Exigido en Requisito 8 de la tarea)
        print("\n=======================================================")
        print(" REPORTE AUDITABLE DE CANTIDADES POR CATEGORÍA DE CMDB")
        print("=======================================================")
        total_real = db.query(models.ConfigurationItem).count()
        print(f"Total Dispositivos Únicos en BD: {total_real}")
        for cat_c, cant in sorted(counts_by_cat.items()):
            print(f"  - [{cat_c}] {cant} dispositivos")
        print("=======================================================\n")

    except Exception as e:
        print(f"[ERROR CRÍTICO EN GENERADOR CMDB]: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador reproducible de CMDB sintética para Software Avanzado.")
    parser.add_argument("--seed", type=int, default=42, help="Semilla determinista del generador (default: 42)")
    parser.add_argument("--count", type=int, default=5000, help="Cantidad meta de dispositivos (default: 5000)")
    parser.add_argument("--clean", action="store_true", help="Limpiar CIs anteriores antes de generar")
    args = parser.parse_args()

    generate_cmdb_data(seed=args.seed, target_count=args.count, clean=args.clean)
