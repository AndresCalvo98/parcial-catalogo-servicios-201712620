# Matriz de Trazabilidad y Pruebas Automatizadas (`docs/PRUEBAS.md`)

**Asignatura:** Software Avanzado | USAC  
**Estudiante:** Andrés Calvo | **Carné:** 201712620  
**Catedrático:** Msc. Marco Tulio Aldana Prillwitz | **GitHub:** `maldanap-usac`  
**Proyecto:** Sistema de Service Desk y Gestión de CMDB bajo Estándares ITIL  
**Framework de Pruebas:** Pytest 9.2.0 sobre Python 3.14 / PostgreSQL 15  
**Cobertura de Escenarios:** 18 / 18 (100% de Aceptación)  

---

## 1. Resumen de Ejecución de la Suite (Harness P01–P18)

La suite de pruebas automatizadas está implementada en `tests/test_main.py` y se ejecuta de forma reproducible tanto en local como dentro del contenedor Docker de producción:

```bash
# Comando de ejecución en entorno contenerizado Docker
docker exec parcial_backend pytest tests/test_main.py -v -s

# Comando de ejecución en host local
pytest tests/test_main.py -v
```

### Reporte de Salida Oficial:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\Andres\Desktop\SA Parcial 2 parte practica\parcial-catalogo-servicios-201712620
collected 18 items

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

## 2. Matriz de Trazabilidad Completa (P01 a P18)

| Código | Escenario y Criterio de Aceptación | Componente Evaluado | Entrada de Prueba | Comportamiento Esperado | Resultado Real | Estado |
|---|---|---|---|---|---|:---:|
| **P01** | **Autenticación local, cierre y usuario inactivo** | `src/auth.py`<br>`src/main.py` | Credenciales válidas (`admin@demo.com`), inválidas (`bad_pass`), usuario inactivo (`inactivo@demo.com`) y logout. | Login exitoso retorna token JWT; login erróneo retorna HTTP 401; usuario inactivo retorna HTTP 403; petición sin token retorna HTTP 401. | Token emitido; credenciales inválidas e inactivas bloqueadas en servidor. | **PASSED** |
| **P02** | **Importación repetible del catálogo (12 N1 / 46 N2)** | `scripts/import_excel.py` | Archivo `data/CatalogoServicios.xlsx` procesado dos veces consecutivas. | 1ª ejecución crea 12 N1 y 46 N2 físicos. 2ª ejecución reporta 0 creados manteniendo 12/46 exactos (Idempotencia). | Exactamente 12 N1 y 46 N2; SE.12 unificado; 0 duplicados en repetición. | **PASSED** |
| **P03** | **Carga de 5,000+ CIs y repetición determinista** | `scripts/generate_cmdb.py` | Ejecución de generación con `--seed 42` y objetivo de 5,000 CIs. Re-ejecución inmediata. | Primera carga genera $\ge 5,000$ CIs con categorías de 3 niveles. Segunda carga con misma semilla actualiza sin duplicar. | Recuento en BD $\ge 5,000$ antes y después de re-ejecutar. | **PASSED** |
| **P04** | **Jerarquía CMDB y rechazo de ciclos** | `src/graph_service.py`<br>`src/main.py` | Categorías L1, L2, L3. Intento de crear ciclo: Categoría A con padre B y B con padre A. | Árbol jerárquico válido aceptado; detección de ciclo rechaza la operación con `HTTP 400 Bad Request`. | Categorías raíz verificadas; ciclo rechazado con mensaje descriptivo de ciclo. | **PASSED** |
| **P05** | **Creación de tickets con validación referencial** | `src/main.py`<br>`src/schemas.py` | Creación de ticket con CI y Servicio N2 válidos vs CI inexistente (ID 999999). | Ticket con referencias válidas retorna HTTP 200/201; referencia a CI inexistente rechazada con HTTP 404 o 400. | Ticket válido insertado; ticket con CI inexistente denegado con código 404. | **PASSED** |
| **P06** | **Asignación de colas, roles y permisos** | `src/main.py`<br>`src/models.py` | Usuario normal intenta tomar ticket de cola especializada sin ser miembro. | Solo agentes autorizados pueden tomar tickets de su respectiva cola; accesos no autorizados retornan HTTP 403. | Política RBAC comprobada en endpoint de gestión de tickets. | **PASSED** |
| **P07** | **Concurrencia atómica al tomar ticket** | `src/main.py`<br>(Bloqueo por fila) | Dos peticiones simultáneas intentan tomar el mismo ticket libre (`POST /tomar`). | Bloqueo `SELECT ... FOR UPDATE` asigna al primer agente y retorna `HTTP 409 Conflict` al segundo. | Primer reclamo asigna ticket; segundo reclamo retorna 409 con mensaje de conflicto. | **PASSED** |
| **P08** | **Transferencia entre colas con auditoría** | `src/main.py`<br>`src/models.py` | Transferencia de ticket de `COLA-N1` a `COLA-N2` con motivo explícito. | Ticket cambia de cola, libera asignación de agente previo y genera registro en `sd_ticket_auditoria`. | Cola actualizada, asignado_id en NULL y bitácora con campo `cola_id` verificada. | **PASSED** |
| **P09** | **Ruta completa de 7 procesos y transiciones prohibidas** | `src/main.py`<br>(Máquina de estados) | Recorrido válido (Nuevo ➔ Asignado ➔ En Progreso ➔ Resuelto ➔ Cerrado) vs salto ilegal (Nuevo ➔ Cerrado). | Ruta válida culmina en Cerrado; salto directo prohibido es rechazado con `HTTP 400 Bad Request`. | Máquina de estados hace cumplir transiciones permitidas y deniega saltos arbitrarios. | **PASSED** |
| **P10** | **Cambio sin aprobación y autoaprobación denegada** | `src/main.py` | Cambio que intenta ejecutarse sin pasar por Aprobado; acceso donde el aprobador es el mismo solicitante. | Cambio no aprobado no puede pasar a En Ejecución (HTTP 400); autoaprobación denegada con HTTP 403. | Ambos controles de gobernanza rechazados en servidor con códigos respectivos. | **PASSED** |
| **P11** | **Eventos E0–E3 y vinculación de incidentes** | `src/main.py` | Registro de evento E2/E3. Segundo evento sobre el mismo componente afectado. | E2/E3 crea automáticamente un ticket de incidente vinculado; evento sucesivo se asocia sin duplicar ticket. | Incidente vinculado creado; 0 duplicados tras segundo reporte sobre el mismo CI. | **PASSED** |
| **P12** | **Registro I0–I6 y reglas complementarias** | `src/main.py` | Creación de incidentes con criticidades I0 a I6 según duración estimada y redundancia. | Clasificación acorde a matriz Lección 25; cálculo automático de severidad y SLA de resolución. | Códigos y plazos de resolución acordes a los umbrales de la lección. | **PASSED** |
| **P13** | **Incidente vinculado a problema y cambio** | `src/main.py` | Creación de Problema asociando incidente; generación de Cambio para solución definitiva. | Trazabilidad completa en grafo relacional: Incidente ➔ Problema (RCA) ➔ Cambio (RFC). | Tablas `sd_ticket_relaciones` reflejan la cadena causa-efecto íntegra. | **PASSED** |
| **P14** | **Recorrido CI-servicio y análisis de impacto** | `src/graph_service.py` | CI origen con dependencias en cascada (`depende_de`) mapeado a Servicio Nivel 2. | Algoritmo DFS retorna la lista de CIs dependientes y los Servicios N2 en riesgo de indisponibilidad. | Identificación precisa de servicios dependientes; ciclo técnico artificial rechazado. | **PASSED** |
| **P15** | **Cierre sin resolución y reapertura auditada** | `src/main.py` | Intento de resolver/cerrar sin campo `resolución`; posterior reapertura justificada. | Cierre sin resolución rechazado con HTTP 400; reapertura reactiva SLA y crea entrada de auditoría. | Obligatoriedad de resolución validada; reapertura con bitácora confirmada. | **PASSED** |
| **P16** | **Filtros y paginación sobre 5,000 dispositivos** | `src/main.py`<br>`src/database.py` | Búsqueda por texto en 5,000 CIs con filtros por categoría y estado; paginación `skip/limit`. | Consulta SQL con índices responde en < 100ms retornando exactamente la página solicitada. | Tiempo de respuesta ágil (< 25ms); paginación consistente sin omisión de registros. | **PASSED** |
| **P17** | **Métricas, pausas y cumplimiento de SLA** | `src/main.py` | Ticket transita por `Pendiente Tercero` acumulando pausa temporal; resolución posterior. | `tiempo_pausado_minutos` se deduce del cálculo de MTTR; cálculo de cumplimiento dentro de norma. | MTTA y MTTR calculados con precisión aritmética; pausas contabilizadas. | **PASSED** |
| **P18** | **Persistencia de catálogo, CMDB y tickets** | `docker-compose.yml`<br>`src/database.py` | Verificación de persistencia mediante almacenamiento en volumen montado `db_data` en PostgreSQL. | Tras desmontar y reiniciar contenedores, todos los registros (catálogo, CIs, tickets) permanecen intactos. | Integridad transaccional y persistencia comprobada. | **PASSED** |
