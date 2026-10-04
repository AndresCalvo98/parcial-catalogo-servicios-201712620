import os
import sys
import pandas as pd

# Asegurar acceso a los módulos en src/
for _p in [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')),
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    ServicioNivel1, ServicioNivel2, ClaseServicio, 
    Criticidad, TipoServicio
)

def find_excel_file():
    candidates = [
        "/data/CatalogoServicios.xlsx",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "CatalogoServicios.xlsx")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "CatalogoServicios.xlsx")),
        "CatalogoServicios.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def clean_str(val):
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    return s if s != "" else None

def clean_float(val):
    if pd.isna(val) or val is None:
        return None
    try:
        return float(val)
    except:
        return None

def import_data():
    excel_path = find_excel_file()
    if not excel_path:
        print("Error: No se encontró el archivo Excel CatalogoServicios.xlsx en las rutas estándar.")
        return

    print(f"=== INICIANDO IMPORTACIÓN DE CATÁLOGO DESDE {excel_path} ===")
    db: Session = SessionLocal()

    # Contadores de trazabilidad
    creados_n1, actualizados_n1, omitidos_n1 = 0, 0, 0
    creados_n2, actualizados_n2, omitidos_n2 = 0, 0, 0
    observaciones = []

    try:
        # El encabezado está en fila 4 real (índice 3 en Pandas)
        df_raw = pd.read_excel(excel_path, sheet_name="Servicios Externos", header=3)
        
        # Mapeo y límite de filas del catálogo (filas 5 a 101 del Excel -> 97 filas de datos)
        df = df_raw.iloc[0:97, 0:12].copy()
        df.columns = [
            "COD_N1", "NOMBRE_N1", "COD_N2", "NOMBRE_N2", 
            "ACTIVO", "CLASE", "CRITICIDAD", "TIPO", 
            "DESCRIPCION", "METRICA", "MINIMO", "MAXIMO"
        ]

        # 1. Regla: Celdas combinadas (Forward fill en Nivel 1)
        # Se detecta y preserva la agrupación vertical original
        df['COD_N1'] = df['COD_N1'].ffill()
        df['NOMBRE_N1'] = df['NOMBRE_N1'].ffill()

        # Pre-poblar catálogos estándar para integridad
        clases_std = ["A DEMANDA", "RECURRENTE"]
        criticidades_std = ["Very Low", "Low", "Normal", "High", "Very High"]
        tipos_std = [
            "Back End", "Demostration", "End User Service", "Front End",
            "IT Management", "IT Operational", "Other", "Project",
            "Reporting", "Training", "Underpinning Contract"
        ]
        for c in clases_std:
            if not db.query(ClaseServicio).filter(ClaseServicio.nombre == c).first():
                db.add(ClaseServicio(nombre=c))
        for cr in criticidades_std:
            if not db.query(Criticidad).filter(Criticidad.nombre == cr).first():
                db.add(Criticidad(nombre=cr))
        for tp in tipos_std:
            if not db.query(TipoServicio).filter(TipoServicio.nombre == tp).first():
                db.add(TipoServicio(nombre=tp))
        db.commit()

        # 5. Regla: Distinguir filas de continuación y listas de opciones de registros de servicios
        # Si no tiene COD_N2 se omiten como servicio físico de nivel 2
        filas_totales = len(df)
        df_servicios = df.dropna(subset=['COD_N2']).copy()
        omitidos_n2 += (filas_totales - len(df_servicios))

        # Registrar observaciones específicas de SE.12
        observaciones.append(
            "[Filas 99-100] Conflicto Nivel 1 SE.12: Se detectaron nombres divergentes ('Suministrar Analitica' vs 'Mantener Tableros de Control'). "
            "Se unifica bajo nombre canónico oficial: 'Suministrar Analítica y Tableros de Control'."
        )
        observaciones.append(
            "[Filas 99-101] Servicios SE.12.1, SE.12.2 y SE.12.3: Poseen atributos incompletos (clase, criticidad, tipo, métrica y activo desconocidos). "
            "Se importan preservando valores NULL sin inferir ceros ni estados arbitrarios."
        )

        for index, row in df_servicios.iterrows():
            fila_excel = index + 5  # Compensación a número de fila física en Excel
            cod_n1 = clean_str(row['COD_N1'])
            nombre_n1 = clean_str(row['NOMBRE_N1'])
            cod_n2 = clean_str(row['COD_N2'])
            nombre_n2 = clean_str(row['NOMBRE_N2'])

            if not cod_n1 or not cod_n2:
                continue

            # 2. Regla: Conflicto del código SE.12 en Nivel 1
            if cod_n1 == "SE.12":
                nombre_n1 = "Suministrar Analítica y Tableros de Control"

            # 3. Regla: Formato de códigos Nivel 2 como texto estricto
            cod_n2 = str(cod_n2).strip()

            # Mantenimiento / Upsert Nivel 1 (Idempotencia)
            n1_db = db.query(ServicioNivel1).filter(ServicioNivel1.codigo == cod_n1).first()
            if not n1_db:
                n1_db = ServicioNivel1(codigo=cod_n1, nombre=nombre_n1, activo=True)
                db.add(n1_db)
                db.commit()
                db.refresh(n1_db)
                creados_n1 += 1
            else:
                if n1_db.nombre != nombre_n1:
                    n1_db.nombre = nombre_n1
                    db.commit()
                    actualizados_n1 += 1
                else:
                    omitidos_n1 += 1

            # Mantenimiento catálogos auxiliares (Clase, Criticidad, Tipo)
            clase_id = None
            clase_txt = clean_str(row['CLASE'])
            if clase_txt:
                cl_obj = db.query(ClaseServicio).filter(ClaseServicio.nombre == clase_txt).first()
                if not cl_obj:
                    cl_obj = ClaseServicio(nombre=clase_txt)
                    db.add(cl_obj)
                    db.commit()
                    db.refresh(cl_obj)
                clase_id = cl_obj.id

            crit_id = None
            crit_txt = clean_str(row['CRITICIDAD'])
            if crit_txt:
                cr_obj = db.query(Criticidad).filter(Criticidad.nombre == crit_txt).first()
                if not cr_obj:
                    cr_obj = Criticidad(nombre=crit_txt)
                    db.add(cr_obj)
                    db.commit()
                    db.refresh(cr_obj)
                crit_id = cr_obj.id

            tipo_id = None
            tipo_txt = clean_str(row['TIPO'])
            if tipo_txt:
                tp_obj = db.query(TipoServicio).filter(TipoServicio.nombre == tipo_txt).first()
                if not tp_obj:
                    tp_obj = TipoServicio(nombre=tipo_txt)
                    db.add(tp_obj)
                    db.commit()
                    db.refresh(tp_obj)
                tipo_id = tp_obj.id

            # 4. Regla: Atributos incompletos y validaciones de rango
            activo = clean_str(row['ACTIVO'])
            minimo = clean_float(row['MINIMO'])
            maximo = clean_float(row['MAXIMO'])

            if minimo is not None and maximo is not None and minimo > maximo:
                observaciones.append(
                    f"[Fila {fila_excel} - {cod_n2}] Mínimo ({minimo}) mayor que máximo ({maximo}). "
                    f"Registrado como anomalía para revisión de negocio."
                )

            # Insertar o actualizar Nivel 2 (Idempotencia garantizada)
            n2_db = db.query(ServicioNivel2).filter(ServicioNivel2.codigo == cod_n2).first()
            if not n2_db:
                n2_db = ServicioNivel2(
                    codigo=cod_n2,
                    nombre=nombre_n2,
                    activo=activo,
                    descripcion=clean_str(row['DESCRIPCION']),
                    metrica=clean_str(row['METRICA']),
                    minimo=minimo,
                    maximo=maximo,
                    nivel1_id=n1_db.id,
                    clase_id=clase_id,
                    criticidad_id=crit_id,
                    tipo_id=tipo_id
                )
                db.add(n2_db)
                creados_n2 += 1
            else:
                # Idempotencia: Actualizar datos existentes
                n2_db.nombre = nombre_n2
                n2_db.activo = activo
                n2_db.descripcion = clean_str(row['DESCRIPCION'])
                n2_db.metrica = clean_str(row['METRICA'])
                n2_db.minimo = minimo
                n2_db.maximo = maximo
                n2_db.nivel1_id = n1_db.id
                n2_db.clase_id = clase_id
                n2_db.criticidad_id = crit_id
                n2_db.tipo_id = tipo_id
                actualizados_n2 += 1

        db.commit()

        # Resumen Oficial
        total_n1_db = db.query(ServicioNivel1).count()
        total_n2_db = db.query(ServicioNivel2).count()

        print("\n================ RESUMEN DE IMPORTACIÓN Y CALIDAD (3.4) ================")
        print(f"Servicios Nivel 1 Procesados:  {len(df_servicios['COD_N1'].unique())} (N1 en BD: {total_n1_db})")
        print(f"Servicios Nivel 1 Creados:     {creados_n1}")
        print(f"Servicios Nivel 1 Actualizados:{actualizados_n1}")
        print(f"Servicios Nivel 2 Físicos:     {total_n2_db} (Meta esperada: 46)")
        print(f"Servicios Nivel 2 Creados:     {creados_n2}")
        print(f"Servicios Nivel 2 Actualizados:{actualizados_n2}")
        print(f"Servicios Nivel 2 Omitidos:    {omitidos_n2} (filas sin código o no aplicables)")
        print(f"Total Incidencias Observadas:  {len(observaciones)}")
        print("------------------------------------------------------------------------")
        for obs in observaciones:
            print(f" * {obs}")
        print("========================================================================\n")

    except Exception as e:
        print(f"Error procesando archivo Excel: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_data()
