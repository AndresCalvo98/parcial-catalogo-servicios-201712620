# Registro y Evaluación de Prompts (Prompt Engineering)

**Asignatura:** Software Avanzado | USAC  
**Estudiante:** Andrés Calvo | **Carné:** 201712620  
**Herramientas / Modelos utilizados:** Antigravity / Gemini 1.5 Pro & Claude 3.5 Sonnet  
**Período de Aplicación:** 01 de Octubre a 04 de Octubre 2026  
**Marco Teórico de Referencia:** Presentación de Clase — Software Avanzado 2026 (Msc. Marco Tulio Aldana Prillwitz), basándose en la taxonomía de Schulhoff et al. (2024), Sahoo et al. (2024), Wei et al. (2022) y Kojima et al. (2022).

---

## 1. Metodología de Diseño de Prompts

Cada instrucción fue construida respetando la anatomía de seis piezas y los patrones de ingeniería de prompts enseñados en clase:
* **Estructura Base:** `ROL + OBJETIVO + CONTEXTO + RESTRICCIONES + FORMATO + CRITERIOS`.
* **Patrón Operativo:** `Contexto → Tarea → Restricciones → Salida` (Plantilla de desarrollo de software).
* **Patrón de Refinamiento:** `Generar → Criticar → Mejorar → Validar`.
* **Rúbrica de Calidad Aplicada:**
  1. *Exactitud:* ¿La respuesta resuelve el requisito técnico sin errores de sintaxis?
  2. *Completitud:* ¿Cubre casos borde (nulos, duplicados, celdas combinadas)?
  3. *Consistencia:* ¿Mantiene esquemas estables entre ejecuciones?
  4. *Eficiencia:* ¿Optimiza el uso de la ventana de contexto sin desperdiciar tokens?

---

## 2. Los 5 Prompts Estructurales Utilizados

### Prompt 1: Análisis Técnico del Excel y Detección de Anomalías
* **Tema:** Análisis del Excel (`CatalogoServicios.xlsx`).
* **Fecha:** 01 de Octubre 2026.
* **Modelo:** Gemini 1.5 Pro.
* **Rol:** Ingeniero de Datos Senior especializado en calidad de ingesta y ETL.
* **Objetivo:** Analizar la estructura física de la hoja "Servicios Externos" del archivo `CatalogoServicios.xlsx`, identificando celdas combinadas, filas de opciones y conflictos de códigos.
* **Contexto Suministrado:** Archivo `CatalogoServicios.xlsx` preservado en `data/` y especificación del caso de trabajo (encabezados en A4:L4, filas 5 a 101, opciones en E112:H122).
* **Instrucciones:** Escribe un script de inspección en Python utilizando Pandas y OpenPyXL para examinar las columnas A a L. Reporta la cantidad de códigos únicos en Nivel 1 y Nivel 2, filas vacías por celdas combinadas y cualquier divergencia de nombres en códigos idénticos.
* **Restricciones:** El archivo original debe tratarse estrictamente como datos pasivos de solo lectura; prohibido alterar o sobreescribir el archivo Excel.
* **Salida Esperada:** Resumen estructurado en consola detallando conteos exactos (12 códigos N1 y 46 N2), rango de datos y diagnóstico del conflicto en `SE.12`.
* **Criterio de Aceptación:** Confirmación de que las filas físicas no equivalen a registros independientes y reporte del conflicto de nombres en la fila 99 y 100 para el código `SE.12`.

---

### Prompt 2: Diseño del Modelo Relacional y Jerarquía Organizacional
* **Tema:** Diseño del modelo de base de datos.
* **Fecha:** 01 de Octubre 2026.
* **Modelo:** Claude 3.5 Sonnet.
* **Rol:** Arquitecto de Software y Base de Datos Relacionales.
* **Objetivo:** Diseñar el modelo relacional en SQLAlchemy para PostgreSQL con soporte para la jerarquía organizacional estricta y el catálogo de servicios en 2 niveles.
* **Contexto Suministrado:** Requisitos funcionales 3.2 y 3.3. Cadena jerárquica: `Empresa → Área → Departamento → Sección → Puesto → Usuario`. Catálogo de servicios con catálogos auxiliares (Clase, Criticidad, Tipo).
* **Instrucciones:** Define las clases de SQLAlchemy en `models.py`. Establece claves primarias, foráneas, índices y relaciones bidireccionales `relationship`. Modela la asignación de cada servicio Nivel 2 a una Sección responsable y opcionalmente a un Usuario responsable perteneciente a esa sección.
* **Restricciones:** Cada registro de la jerarquía debe tener un único padre; los códigos subordinados deben ser únicos dentro de su padre; la empresa del usuario debe derivarse de su jerarquía (evitar redundancias contradictorias).
* **Salida Esperada:** Archivo `src/models.py` completo y modular, compatible con SQLAlchemy 2.0 y PostgreSQL 15.
* **Criterio de Aceptación:** Generación exitosa de las tablas relacionales sin ciclos foráneos ni registros huérfanos.

---

### Prompt 3: Autenticación, Autorización Local y Seguridad Criptográfica
* **Tema:** Autenticación y autorización.
* **Fecha:** 02 de Octubre 2026.
* **Modelo:** Claude 3.5 Sonnet.
* **Rol:** Especialista en Ciberseguridad y Backend FastAPI.
* **Objetivo:** Implementar un subsistema de autenticación local con JWT y hash seguro de contraseñas con sal, aplicando control de acceso basado en roles (RBAC).
* **Contexto Suministrado:** Requisito 3.1 del parcial. Roles: `administrador` (mantenimiento total) y `consulta` (solo lectura). Cuentas de evaluación: `admin@demo.com` / `admin123` y `normal@demo.com` / `clave`.
* **Instrucciones:** Desarrolla `src/auth.py` y las dependencias de seguridad en `src/main.py`. Utiliza `bcrypt` nativo con sal única para hashear y verificar contraseñas. Implementa endpoints `/token`, `/logout`, `/usuarios/me` y dependencias `get_current_user` y `admin_required`. Valida que usuarios con `activo=False` no puedan iniciar sesión ni realizar peticiones.
* **Restricciones:** Prohibido el uso de proveedores OAuth externos (Google/GitHub); prohibido texto plano o cifrado simétrico reversible; la protección debe ocurrir en el servidor (HTTP 401 y HTTP 403).
* **Salida Esperada:** Código en `auth.py` y rutas de FastAPI con OpenAPI Swagger documentado.
* **Criterio de Aceptación:** Superación de los escenarios P01, P02 y P03 ante intentos de login inválido, usuario inactivo y usuario de consulta intentando operaciones de escritura.

---

### Prompt 4: Ingesta Idempotente y Tratamiento de Calidad de Datos
* **Tema:** Importación y calidad de datos.
* **Fecha:** 02 de Octubre 2026.
* **Modelo:** Gemini 1.5 Pro.
* **Rol:** Ingeniero de Software Backend / Data Pipeline.
* **Objetivo:** Construir un script automatizado (`scripts/import_excel.py`) que ingeste el catálogo desde `CatalogoServicios.xlsx` resolviendo celdas combinadas, conflictos de código y atributos incompletos.
* **Contexto Suministrado:** Hoja "Servicios Externos", delimitación de filas 5 a 101, hallazgo de celdas combinadas en Nivel 1 y conflicto de `SE.12` en filas 99 y 100.
* **Instrucciones:** Implementa `import_data()` con Pandas y SQLAlchemy. Aplica `ffill()` en `COD_N1` y `NOMBRE_N1`. Resuelve el conflicto de `SE.12` en Nivel 1 asignando el nombre canónico oficial *"Suministrar Analítica y Tableros de Control"* y registrando la observación. Preserva los 3 servicios dependientes (SE.12.1, SE.12.2, SE.12.3) con sus nombres y códigos originales como texto. Conserva atributos faltantes como `null` sin inventar valores. Implementa lógica de upsert para garantizar idempotencia.
* **Restricciones:** No alterar el Excel original; no inventar métricas, criticidades ni umbrales ausentes; no permitir duplicados en segundas corridas.
* **Salida Esperada:** Script ejecutable que imprima un resumen formal de registros procesados, creados, actualizados, omitidos y observaciones.
* **Criterio de Aceptación:** Conteo exacto de 12 códigos de Nivel 1 y 46 servicios físicos de Nivel 2, con idempotencia verificable (`conteo_inicial == conteo_final`).

---

### Prompt 5: Dockerización, Persistencia y Harness Engineering
* **Tema:** Docker y pruebas automatizadas (Harness).
* **Fecha:** 03 de Octubre 2026.
* **Modelo:** Gemini 1.5 Pro.
* **Rol:** Ingeniero DevOps y QA Automation.
* **Objetivo:** Orquestar el entorno en Docker Compose con base de datos PostgreSQL persistente y construir la suite de pruebas unitarias y de integración que valide los 12 criterios de aceptación (P01 a P12).
* **Contexto Suministrado:** Requisitos de la Sección 5 y tabla de escenarios P01 a P12 de la Sección 6.
* **Instrucciones:** Diseña `Dockerfile`, `docker-compose.yml`, `compose.yaml` y `tests/test_main.py` con Pytest y TestClient. Configura healthcheck en PostgreSQL para que FastAPI arranque únicamente cuando la base esté lista. Automatiza los 12 escenarios de prueba con aislamiento de datos y código de salida determinista (cero en éxito).
* **Restricciones:** Todo debe ejecutarse dentro de contenedores mediante `docker compose up --build -d` sin requerir dependencias en el host; la persistencia debe mantenerse mediante el volumen `db_data`.
* **Salida Esperada:** Configuración Docker funcional y suite de pruebas con 12 tests observables.
* **Criterio de Aceptación:** Ejecución de `docker exec parcial_backend pytest tests/test_main.py -v` con resultado de `12 passed in <10s` (código de salida 0).

---

## 3. Registro de Iteraciones de Mejora Empírica

### Iteración 1: Resolución de Celdas Combinadas y Conflicto SE.12 en Ingesta
* **Herramienta / Modelo:** Gemini 1.5 Pro.
* **Fecha:** 02 de Octubre 2026.
* **Prompt Inicial:**
  > *"Lee CatalogoServicios.xlsx con pandas e inserta cada fila en la tabla de servicios de la base de datos."*
* **Problema Observado:**
  1. Debido a las celdas combinadas de Excel, las filas 6 a 8 tenían `NaN` en `COD_N1` y `NOMBRE_N1`, provocando errores de integridad referencial.
  2. En las filas 99 y 100, la IA intentó insertar dos registros con el código `SE.12`, provocando un fallo de clave única (`UniqueViolation`).
  3. Peor aún, una versión preliminar confundió el conflicto de Nivel 1 con el de Nivel 2 y eliminó el servicio `SE.12.3`, dando como resultado 45 servicios en lugar de los 46 requeridos.
* **Prompt Revisado:**
  > *"Escribe un script de importación con Pandas y SQLAlchemy para 'CatalogoServicios.xlsx' hoja 'Servicios Externos'. Aplica df['COD_N1'].ffill() y df['NOMBRE_N1'].ffill() para propagar el contexto padre en celdas combinadas. Descarta filas sin 'COD_N2' para ignorar notas de pie. Para el código Nivel 1 'SE.12', unifica el nombre canónico bajo 'Suministrar Analítica y Tableros de Control' y emite una observación trazable. En Nivel 2, preserva intactos los 3 servicios (SE.12.1, SE.12.2 y SE.12.3) con sus nombres originales y atributos vacíos como NULL. Implementa upsert para que re-ejecutar el script no genere duplicados."*
* **Resultado Comprobado:**
  Se importaron exactamente **12 códigos de Nivel 1** y **46 servicios de Nivel 2**, manteniendo intacta la trazabilidad y logrando idempotencia total al repetir la ejecución.

---

### Iteración 2: Incompatibilidad Criptográfica Passlib y Aislamiento de Pruebas
* **Herramienta / Modelo:** Claude 3.5 Sonnet.
* **Fecha:** 03 de Octubre 2026.
* **Prompt Inicial:**
  > *"Implementa hashing de contraseñas con passlib CryptContext bcrypt y escribe los tests en test_main.py creando una empresa EMP-P04 y probando los endpoints."*
* **Problema Observado:**
  1. En el contenedor con Python 3.11 y la última versión compilada de `bcrypt` (v4.1+), `passlib` generó una excepción crítica (`ValueError: password cannot be longer than 72 bytes`), quebrando el login.
  2. En `test_main.py`, al re-ejecutar las pruebas consecutivamente, `test_P04` y `test_P11` fallaban con `400 Bad Request` porque `EMP-P04` y `user_a@demo.com` ya existían de la ejecución previa, violando el principio de aislamiento e idempotencia de Harness Engineering.
* **Prompt Revisado:**
  > *"Reescribe auth.py eliminando completamente passlib y usando directamente bcrypt nativo con bcrypt.gensalt() y bcrypt.hashpw(). En tests/test_main.py, implementa aislamiento de datos: antes de cada prueba que cree entidades (P04, P05, P11), consulta y limpia los registros previos de prueba con esos códigos dentro de la transacción, de manera que la suite sea 100% idempotente y pueda ejecutarse indefinidamente sin colisiones de base de datos."*
* **Resultado Comprobado:**
  El sistema de autenticación opera sin advertencias de deprecación con sal criptográfica segura. La suite de pruebas de Harness Engineering ejecuta los 12 escenarios de aceptación con **12 passed** de forma determinista y reproducible (código de salida 0).
