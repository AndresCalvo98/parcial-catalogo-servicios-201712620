# Sistema Integral de Gestión del Catálogo de Servicios TI, CMDB y Service Desk (ITIL)

> **Asignatura:** Software Avanzado | USAC  
> **Estudiante:** Andrés Calvo — Carné `201712620`  
> **Catedrático:** Msc. Marco Tulio Aldana Prillwitz | **GitHub:** `maldanap-usac`  
> **Repositorio:** `parcial-catalogo-servicios-201712620`  
> **Entrega:** Parcial 3 / Tarea Service Desk  

---

## 🚀 Descripción General del Sistema

Plataforma empresarial de gestión tecnológica que integra de extremo a extremo:
1. **Catálogo de Servicios de TI:** 12 códigos Nivel 1 y 46 servicios físicos Nivel 2 extraídos e importados de forma idempotente desde `CatalogoServicios.xlsx` con unificación canónica de `SE.12`.
2. **Estructura Organizacional:** Jerarquía corporativa estricta de 6 niveles (`Empresa ➔ Área ➔ Depto ➔ Sección ➔ Puesto ➔ Usuario`) con asignación obligatoria de responsables.
3. **CMDB a Escala Real ($\ge 5,000$ CIs):** Base de datos de configuración estructurada en 3 niveles taxonómicos (Familia, Clase, Tipo según Lección 22), relaciones topológicas acíclicas (DAG) y vinculación a los 46 servicios N2.
4. **Graph Engineering:** Algoritmo DFS para detección y rechazo de ciclos en dependencias, junto con cálculo instantáneo de impacto en cascada hacia los servicios de negocio.
5. **Service Desk Multiproceso (ITIL):** Implementación integral de los **7 procesos de TI** (Nuevos Servicios, Cambios con aprobación CAB, Incidentes I0–I6, Eventos E0–E3, Problemas con KEDB, Accesos con segregación y Requisiciones).
6. **Gestión de Colas y Concurrencia Atómica:** Bloqueo pesimista a nivel de fila (`SELECT ... FOR UPDATE` retornando `HTTP 409 Conflict`) al tomar tickets.
7. **Portales Web Especializados:** Consola de Agente/Mesa de Ayuda, Portal de Autoservicio con Base de Conocimiento (FAQ Nivel 0) y Dashboard en vivo de SLAs (MTTA, MTTR, cumplimiento %).
8. **Harness Engineering (P01–P18):** Suite de 18 pruebas automatizadas de aceptación con 100% de éxito.

---

## 🛠️ Pila Tecnológica

* **Backend:** FastAPI (Python 3.11 / 3.14) con validación estricta de esquemas Pydantic V2.
* **Base de Datos:** PostgreSQL 15 con transaccionalidad ACID e integridad referencial.
* **ORM:** SQLAlchemy 2.0 (consultas parametrizadas y bloqueos de concurrencia).
* **Seguridad:** Autenticación local con JWT y algoritmos de salado/hash `bcrypt`.
* **Contenedores:** Docker y Docker Compose para ejecución reproducible sin dependencias del host.
* **Frontend:** Single Page Application (SPA) en HTML5, CSS3 moderno y Vanilla JS (sin frameworks pesados).
* **Test Harness:** Pytest 9.2.0 automatizado con TestClient.

---

## 📋 Requisitos Previos

* **Docker Desktop** (versión 24.x o superior) con Docker Compose habilitado.
* Puertos libres en el anfitrión: **`8000`** (Web / API) y **`5432`** (PostgreSQL).

---

## ⚡ Guía de Inicio Rápido (Despliegue en 3 Pasos)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/AndresCalvo98/parcial-catalogo-servicios-201712620.git
cd parcial-catalogo-servicios-201712620
```

### 2. Levantar el Ecosistema en Docker
```bash
docker compose up --build -d
```
> El contenedor de backend esperará automáticamente a que la base de datos PostgreSQL esté lista (`healthy`) antes de inicializar la API.

### 3. Población Inicial de Datos (Demostración y Evaluación)
Ejecuta los siguientes comandos para crear las cuentas de prueba, importar el catálogo de Excel y generar los 5,000 CIs deterministas:

```bash
# 1. Crear estructura organizacional, cuentas de prueba, 7 colas y tickets demo
docker exec -it parcial_backend python scripts/create_admin.py

# 2. Ingesta idempotente del catálogo original de Excel (12 N1 / 46 N2)
docker exec -it parcial_backend python scripts/import_excel.py

# 3. Generación determinista de al menos 5,000 elementos de configuración (CMDB)
docker exec -it parcial_backend python scripts/generate_cmdb.py --seed 42 --count 5000
```

---

## 👥 Cuentas de Evaluación Rápida

La plataforma incluye 6 cuentas de demostración preconfiguradas localmente para evaluar todos los roles y procesos sin necesidad de registrarse:

| Usuario / Correo | Contraseña | Rol en Sistema | Función y Alcance |
|---|---|---|---|
| `admin@demo.com` | `admin123` | **administrador** | Control total de usuarios, organigrama, CMDB y catálogos. |
| `agente1@demo.com` | `clave123` | **consulta / agente** | Agente de Soporte Nivel 1 (Mesa de Ayuda y Despacho). |
| `agente2@demo.com` | `clave123` | **consulta / agente** | Especialista de Soporte Nivel 2 y Cambios. |
| `aprobador@demo.com` | `clave123` | **consulta / aprobador** | Integrante del CAB y Jefatura para aprobación de Cambios y Accesos. |
| `solicitante@demo.com` | `clave123` | **consulta / solicitante**| Usuario final para autoservicio, consulta de FAQs y apertura de tickets. |
| `normal@demo.com` | `clave` | **consulta** | Usuario estándar de solo lectura (sin permisos de edición). |

> 💡 En la pantalla de inicio de sesión de la aplicación web se dispone de botones de **Acceso Rápido** para ingresar con cualquiera de estas cuentas con un solo clic.

---

## 🌐 Enlaces del Entorno en Ejecución

* **Aplicación Web Principal:** [http://localhost:8000](http://localhost:8000)
* **Documentación Interactiva Swagger / OpenAPI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Especificación ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Endpoint de Ejecución del Test Harness:** [http://localhost:8000/harness/ejecutar](http://localhost:8000/harness/ejecutar)

---

## 🧪 Ejecución de la Suite de Pruebas (Harness P01–P18)

Para comprobar de forma 100% automatizada el cumplimiento de los 18 criterios de aceptación, ejecuta:

```bash
docker exec parcial_backend pytest tests/test_main.py -v
```

### Salida Esperada:
```text
tests/test_main.py::test_P01_autenticacion_cierre_y_usuario_inactivo PASSED   [  5%]
tests/test_main.py::test_P02_importacion_repetible_catalogo PASSED           [ 11%]
tests/test_main.py::test_P03_carga_5000_dispositivos_unicos_y_repeticion PASSED [ 16%]
tests/test_main.py::test_P04_jerarquia_cmdb_y_rechazo_de_ciclos PASSED       [ 22%]
tests/test_main.py::test_P05_creacion_tickets_referencias_validas_e_invalidas PASSED [ 27%]
tests/test_main.py::test_P06_asignacion_cola_a_roles_y_usuarios_politica_permisos PASSED [ 33%]
tests/test_main.py::test_P07_ordenamiento_reproducible_y_concurrencia_tomar_ticket PASSED [ 38%]
tests/test_main.py::test_P08_transferencia_entre_colas_con_historial_y_validacion PASSED [ 44%]
tests/test_main.py::test_P09_ejecucion_ruta_completa_7_procesos_y_transiciones_invalidas PASSED [ 50%]
tests/test_main.py::test_P10_cambio_sin_aprobacion_y_acceso_autoaprobado_rechazados PASSED [ 55%]
tests/test_main.py::test_P11_eventos_E0_E3_y_vinculacion_incidentes_sin_duplicar PASSED [ 61%]
tests/test_main.py::test_P12_registro_I0_I6_y_reglas_complementarias PASSED  [ 66%]
tests/test_main.py::test_P13_incidente_vinculado_a_problema_y_cambio PASSED   [ 72%]
tests/test_main.py::test_P14_recorrido_ci_servicio_y_manejo_de_ciclos PASSED [ 77%]
tests/test_main.py::test_P15_cierre_sin_resolucion_reapertura_y_bitacora PASSED [ 83%]
tests/test_main.py::test_P16_filtros_y_paginacion_5000_dispositivos PASSED   [ 88%]
tests/test_main.py::test_P17_indicadores_con_datos_controlados PASSED        [ 94%]
tests/test_main.py::test_P18_reinicio_de_contenedores_y_persistencia PASSED   [100%]

====================== 18 passed in 7.21s ======================
```

---

## 📚 Índice de Documentación Técnica Formal

| Documento | Ubicación | Contenido y Alcance |
|---|---|---|
| **Informe de Arquitectura** | [`docs/RESOLUCION.md`](docs/RESOLUCION.md) | Justificación de tecnologías, decisiones de diseño, concurrencia y seguridad. |
| **Modelo y Diccionario de Datos** | [`docs/MODELO.md`](docs/MODELO.md) | Diagrama ER integral Mermaid, diccionario de campos y mapeo de taxonomía. |
| **Especificación de Procesos ITIL** | [`docs/PROCESOS.md`](docs/PROCESOS.md) | Ciclos de vida de los 7 procesos, diagramas de estado, SLAs y niveles de escalamiento. |
| **Disciplinas de Ingeniería con IA** | [`docs/IA.md`](docs/IA.md) | 8 prompts reales, 2 mejoras comparativas, 3 ciclos de loop engineering y grafos. |
| **Matriz de Pruebas Automatizadas** | [`docs/PRUEBAS.md`](docs/PRUEBAS.md) | Matriz de trazabilidad exhaustiva de los escenarios P01 a P18. |
| **Reglas de Contexto y Asistentes** | [`AGENTS.md`](AGENTS.md) | Reglas operativas, guardrails de seguridad y trazabilidad de actualizaciones. |
