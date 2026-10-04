import os
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    ServicioNivel1, ServicioNivel2, ClaseServicio, 
    Criticidad, TipoServicio
)

EXCEL_PATH = "/data/CatalogoServicios.xlsx" 

def clean_code(val):
    if pd.isna(val):
        return None
    return str(val).strip()

def clean_text(val):
    if pd.isna(val):
        return None
    return str(val).strip()

def clean_float(val):
    if pd.isna(val):
        return None
    try:
        return float(val)
    except:
        return None

def import_data():
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encontró el archivo Excel en {EXCEL_PATH}")
        print("Asegúrate de que 'CatalogoServicios.xlsx' esté en la carpeta 'data/'.")
        return

    print(f"Iniciando importación desde {EXCEL_PATH}")
    db: Session = SessionLocal()
    
    try:
        # Celdas combinadas: forward fill en A y B (Nivel 1)
        # La tabla comienza en fila 4 real (índice 3 en Pandas)
        df = pd.read_excel(EXCEL_PATH, sheet_name="Servicios Externos", header=3)
        
        # Mapeo y límite de filas (hasta fila 101, pero como quitamos encabezados es hasta índice ~96)
        df = df.iloc[0:97, 0:12] 
        df.columns = ["COD_N1", "NOMBRE_N1", "COD_N2", "NOMBRE_N2", "ACTIVO", "CLASE", "CRITICIDAD", "TIPO", "DESCRIPCION", "METRICA", "MINIMO", "MAXIMO"]
        
        # 1. Regla: Recuperar valor de celda principal dentro de rango combinado
        df['COD_N1'] = df['COD_N1'].ffill()
        df['NOMBRE_N1'] = df['NOMBRE_N1'].ffill()
        
        # 5. Regla: Filas de continuación (distinguirlas de los registros)
        # Las filas que no tienen COD_N2 se ignoran como servicio independiente
        df = df.dropna(subset=['COD_N2'])

        # Contadores de trazabilidad
        creados_n1, creados_n2 = 0, 0
        observaciones = []

        for index, row in df.iterrows():
            cod_n1 = clean_code(row['COD_N1'])
            nombre_n1 = clean_text(row['NOMBRE_N1'])
            cod_n2 = clean_code(row['COD_N2'])
            nombre_n2 = clean_text(row['NOMBRE_N2'])
            
            # 2. Regla: Conflicto del código SE.12
            if cod_n2 == "SE.12":
                if nombre_n2 in ["Suministrar Analitica", "Mantener Tableros de Control"]:
                    nombre_canonico = "Suministrar Analítica y Tableros de Control"
                    observaciones.append(f"Regla SE.12 aplicada: El código {cod_n2} ({nombre_n2}) fue unificado bajo '{nombre_canonico}'.")
                    nombre_n2 = nombre_canonico
                    
                    # Evitar duplicados de SE.12 en la misma importación
                    existente = db.query(ServicioNivel2).filter(ServicioNivel2.codigo == cod_n2).first()
                    if existente:
                        continue 
            
            # Mantenimiento de Nivel 1
            n1_db = db.query(ServicioNivel1).filter(ServicioNivel1.codigo == cod_n1).first()
            if not n1_db:
                n1_db = ServicioNivel1(codigo=cod_n1, nombre=nombre_n1)
                db.add(n1_db)
                db.commit()
                db.refresh(n1_db)
                creados_n1 += 1
                
            # Mantenimiento de catálogos (Clase, Criticidad, Tipo)
            clase_txt = clean_text(row['CLASE'])
            clase_id = None
            if clase_txt:
                clase_db = db.query(ClaseServicio).filter(ClaseServicio.nombre == clase_txt).first()
                if not clase_db:
                    clase_db = ClaseServicio(nombre=clase_txt)
                    db.add(clase_db)
                    db.commit()
                    db.refresh(clase_db)
                clase_id = clase_db.id

            crit_txt = clean_text(row['CRITICIDAD'])
            crit_id = None
            if crit_txt:
                crit_db = db.query(Criticidad).filter(Criticidad.nombre == crit_txt).first()
                if not crit_db:
                    crit_db = Criticidad(nombre=crit_txt)
                    db.add(crit_db)
                    db.commit()
                    db.refresh(crit_db)
                crit_id = crit_db.id

            tipo_txt = clean_text(row['TIPO'])
            tipo_id = None
            if tipo_txt:
                tipo_db = db.query(TipoServicio).filter(TipoServicio.nombre == tipo_txt).first()
                if not tipo_db:
                    tipo_db = TipoServicio(nombre=tipo_txt)
                    db.add(tipo_db)
                    db.commit()
                    db.refresh(tipo_db)
                tipo_id = tipo_db.id

            # 4. Regla: Atributos incompletos (conservar nulos, no inventar datos)
            activo = clean_text(row['ACTIVO'])
            
            # Validación mínimo <= máximo
            minimo = clean_float(row['MINIMO'])
            maximo = clean_float(row['MAXIMO'])
            if minimo is not None and maximo is not None:
                if minimo > maximo:
                    observaciones.append(f"Validación en {cod_n2}: El mínimo ({minimo}) es mayor que el máximo ({maximo}). Se importará como anomalía observada.")
            
            # Creación o actualización Nivel 2 (Idempotencia)
            n2_db = db.query(ServicioNivel2).filter(ServicioNivel2.codigo == cod_n2).first()
            if not n2_db:
                n2_db = ServicioNivel2(
                    codigo=cod_n2,
                    nombre=nombre_n2,
                    activo=activo,
                    descripcion=clean_text(row['DESCRIPCION']),
                    metrica=clean_text(row['METRICA']),
                    minimo=minimo,
                    maximo=maximo,
                    nivel1_id=n1_db.id,
                    clase_id=clase_id,
                    criticidad_id=crit_id,
                    tipo_id=tipo_id
                )
                db.add(n2_db)
                creados_n2 += 1
                
        db.commit()
        
        print("\n--- REPORTE DE CALIDAD E IMPORTACIÓN ---")
        print(f"Servicios Nivel 1 insertados: {creados_n1} (Se esperaban 12 códigos)")
        print(f"Servicios Nivel 2 insertados: {creados_n2} (Se esperaban 46 servicios físicos)")
        print("\nIncidencias y Reglas de Trazabilidad Documentadas:")
        for obs in observaciones:
            print(f" [!] {obs}")
            
    except Exception as e:
        print(f"Error crítico procesando Excel: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_data()
