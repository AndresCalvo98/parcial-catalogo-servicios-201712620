# Informe Técnico de Resolución y Decisiones de Arquitectura (`docs/RESOLUCION.md`)

**Asignatura:** Software Avanzado | USAC  
**Estudiante:** Andrés Calvo | **Carné:** 201712620  
**Catedrático:** Msc. Marco Tulio Aldana Prillwitz | **GitHub:** `maldanap-usac`  
**Proyecto:** Sistema Integral de Catálogo de Servicios TI, CMDB y Service Desk (ITIL)  
**Repositorio:** `parcial-catalogo-servicios-201712620`  
**Entrega:** Parcial 3 / Tarea Service Desk  

---

## 1. Problema, Alcance y Supuestos de Negocio

### 1.1. Planteamiento del Problema
En la gestión moderna de servicios de TI (**ITSM** - *IT Service Management*), marcos de trabajo reconocidos internacionalmente como **ITIL** (*Information Technology Infrastructure Library*) y **SACM** (*Service Asset and Configuration Management*) exigen que la provisión de valor tecnológico esté soportada en tres pilares inseparables:
1. **Catálogo de Servicios de TI:** Visibilidad clara de los servicios de negocio acordados y sus métricas de calidad.
2. **Base de Datos de Gestión de la Configuración (CMDB):** Un modelo topológico preciso y acíclico de todos los elementos tecnológicos (CIs) y sus interdependencias.
3. **Mesa de Servicios (Service Desk):** Un punto único de contacto (**SPOC**) capaz de canalizar peticiones, incidentes y cambios a través de colas especializadas y niveles de soporte (Nivel 0 al 4).

La organización objeto de estudio operaba históricamente de manera fragmentada: su catálogo de servicios residía en una hoja de cálculo (`CatalogoServicios.xlsx`) con celdas combinadas y códigos en conflicto (`SE.12`), carecía de una CMDB automatizada y no disponía de un sistema transaccional para despachar tickets con garantías de concurrencia y cumplimiento de SLAs.

### 1.2. Alcance del Sistema
La plataforma desarrollada integra completamente:
* **Catálogo de Servicios TI (Parcial 2):** Ingesta repetible e idempotente del archivo Excel original; 12 códigos N1 y 46 servicios físicos N2; jerarquía organizacional (`Empresa ➔ Área ➔ Depto ➔ Sección ➔ Puesto ➔ Usuario`); asignación obligatoria de sección responsable; autenticación local con bcrypt y JWT.
* **CMDB a Escala Real ($\ge 5,000$ CIs) (Lección 22):** Generación determinista y configurable mediante semilla (`--seed`); taxonomía jerárquica en 3 niveles (Familia, Clase, Tipo); relaciones de dependencia (`depende_de`, `alojado_en`, `conectado_a`) con detección estricta de ciclos (DAG); vinculación de CIs a los 46 servicios N2 de catálogo.
* **Service Desk Multiproceso (Lección 25):** Implementación de los **7 procesos ITIL obligatorios** (Nuevos Servicios, Cambios, Incidentes I0–I6, Eventos E0–E3, Problemas, Accesos y Requisiciones); enrutamiento por colas técnicas; control de concurrencia atómica al tomar tickets (`SELECT ... FOR UPDATE` retornando `HTTP 409`); portal de autoservicio (FAQ Nivel 0); cálculo de métricas MTTA, MTTR y pausas de reloj en `Pendiente Tercero`.
* **Ingeniería Asistida por Inteligencia Artificial:** Aplicación y documentación auditable de las 5 disciplinas: Context Engineering, Prompt Engineering, Harness Engineering, Loop Engineering y Graph Engineering.

### 1.3. Supuestos y Decisiones de Negocio
1. **Inmutabilidad de los Archivos Fuente:** Los archivos `data/CatalogoServicios.xlsx` y `Leccion 22/CMDB.xlsx` se preservan intactos sin alteración manual alguna, asegurando que cualquier evaluador pueda reproducir los procesos de ingesta y validación desde cero.
2. **Nombre Canónico Unificado para `SE.12`:** Para resolver la duplicidad en las filas 99 y 100 (*"Suministrar Analitica"* vs *"Mantener Tableros de Control"*), se consolida el nombre canónico **"Suministrar Analítica y Tableros de Control"**, emitiendo la observación formal correspondiente en la bitácora de importación y preservando sus 3 servicios hijos (`SE.12.1`, `SE.12.2`, `SE.12.3`).
3. **Tratamiento de Valores Ausentes:** En las filas 99 a 101, los atributos faltantes se almacenan como `NULL` en PostgreSQL; está estrictamente prohibido inventar valores o asumir ceros.
4. **Aciclicidad Estricta en Dependencias Técnicas:** Las relaciones `depende_de` y `alojado_en` no toleran ciclos (forman un Grafo Acíclico Dirigido - DAG). Si se intenta insertar una dependencia que cierre un bucle, la API la rechaza inmediatamente con `HTTP 400 Bad Request`. Las relaciones de red `conectado_a` sí toleran topologías malladas de telecomunicaciones.
5. **Gobernanza y Segregación de Funciones:** 
   - Un cambio no puede ejecutarse sin previa aprobación formal del CAB.
   - En peticiones de acceso, el usuario aprobador no puede ser la misma persona que solicita el permiso (se rechaza con `HTTP 403 Forbidden`).
   - El cierre de un ticket exige documentar la solución aplicada.

---

## 2. Arquitectura del Sistema y Justificación Tecnológica

El sistema implementa una **Arquitectura en Capas Desacoplada** completamente contenerizada en Docker:

```
[ Cliente Web / Navegador SPA ]
        ▲
        │ HTTP REST / JSON / Bearer JWT
        ▼
[ Servidor Web & API: FastAPI (Python 3.11 / 3.14) ]
   ├── Módulo de Autenticación Local (bcrypt + JWT stateless)
   ├── Controladores de Catálogo TI & Estructura Organizacional
   ├── Controladores de CMDB & Motor de Grafos (DFS / Cycle Detection)
   ├── Máquina de Estados de los 7 Procesos ITIL & Gestión de Colas
   └── Motor de Métricas, SLAs (MTTA / MTTR) y Portal FAQ Nivel 0
        ▲
        │ SQLAlchemy 2.0 ORM (Consultas Parametrizadas / FOR UPDATE)
        ▼
[ Motor de Base de Datos: PostgreSQL 15 ]
   ├── Integridad Referencial Estricta (FKs, Restricciones CHECK y UNIQUE)
   ├── Índices B-Tree en CIs (código, IP, número de serie, categoría)
   └── Persistencia Transaccional en Volumen Docker (`db_data`)
```

### Justificación de Tecnologías Seleccionadas
* **FastAPI:** Selección ideal por su alto rendimiento asíncrono, validación estricta de esquemas con Pydantic V2 y generación nativa de documentación OpenAPI/Swagger en `/docs`.
* **PostgreSQL 15:** Motor relacional robusto con soporte nativo para transacciones ACID, aislamiento de transacciones y bloqueo a nivel de fila (`FOR UPDATE`), indispensable para evitar carreras en la toma de tickets.
* **SQLAlchemy 2.0:** Abstracción declarativa que previene vulnerabilidades de inyección SQL mediante consultas parametrizadas.
* **Bcrypt:** Algoritmo estándar de la industria con factor de costo configurable y sal única por usuario, garantizando que ninguna credencial se guarde en texto plano o cifrado reversible.
* **Docker & Docker Compose:** Permite el levantamiento instantáneo de todo el ecosistema con un único comando (`docker compose up --build -d`), aislando dependencias y garantizando reproducibilidad en cualquier máquina evaluadora.

---

## 3. Estrategia de Concurrencia y Control de Bloqueos

Uno de los desafíos técnicos más críticos en un Service Desk de alto volumen es evitar que dos agentes asignen el mismo ticket simultáneamente (*race condition*). 

### Implementación del Bloqueo Pesimista
En el endpoint `POST /api/tickets/{id}/tomar`:
1. La consulta SQLAlchemy inicia una transacción explícita con bloqueo de fila:
   ```python
   ticket = db.query(Ticket).filter(Ticket.id == ticket_id).with_for_update().first()
   ```
2. Si otro agente intenta tomar el ticket simultáneamente, la base de datos bloquea su lectura hasta que la primera transacción concluya (`COMMIT` o `ROLLBACK`).
3. Al liberarse el bloqueo, la segunda petición detecta que `ticket.asignado_id` ya no es nulo o que el estado ya cambió, abortando de inmediato y respondiendo al segundo usuario con:
   ```json
   {
       "detail": "El ticket ya ha sido tomado por otro agente o no está disponible para asignación directa."
   }
   ```
   Acompañado del código de estado **`HTTP 409 Conflict`**. Este comportamiento es verificado formalmente por el escenario automatizado **`P07`**.

---

## 4. Seguridad, Roles y Autorización (RBAC)

El sistema opera bajo un esquema de **Role-Based Access Control (RBAC)** local:
* **Rol `administrador`:** Acceso total para dar de alta/baja usuarios, modificar la estructura organizacional, reconfigurar colas de servicio y gestionar el catálogo maestro.
* **Rol `consulta` / `solicitante`:** Acceso de lectura sobre el catálogo de servicios, elementos de la CMDB y consulta de tickets propios. Denegación estricta (`HTTP 403 Forbidden`) en operaciones mutativas (POST, PUT, DELETE) y visualización de hashes o credenciales internas.
* **Seguridad en Servidor:** Las restricciones se validan en cada endpoint de la API mediante la inyección `Depends(require_admin)` o comprobaciones de membresía en colas. Ocultar botones en la interfaz gráfica es únicamente una conveniencia estética; la seguridad se ejerce de forma inquebrantable en backend.
* **Inactivación de Usuarios:** Si un usuario es marcado con `activo = False`, la función `get_current_active_user` deniega inmediatamente cualquier transacción subsiguiente con `HTTP 403 Forbidden`.

---

## 5. Supuestos, Limitaciones y Mejoras Futuras

* **Volumen de CMDB:** El generador sintético puebla determinísticamente 5,000 CIs. La base de datos y los índices B-Tree están diseñados para escalar a más de 100,000 CIs sin degradación en los tiempos de respuesta paginados (< 50 ms).
* **Topologías de Red vs Dependencias:** La distinción semántica entre `depende_de` (estricto DAG sin ciclos) y `conectado_a` (mallas permitidas) refleja la realidad de infraestructuras complejas con alta disponibilidad (HA).
* **Alcance Excluido:** Conforme a las instrucciones del parcial, no se implementó facturación contable, consumo de saldos ni pasarelas de pago de servicios.

---

## 6. Lista de Chequeo para la Defensa del Parcial

| Requisito Evaluado | Implementación Verificable | Evidencia / Endpoint / Archivo |
|---|---|---|
| **Contenedorización Docker** | Despliegue reproducible con PostgreSQL y backend | `docker compose up --build -d` |
| **Credenciales de Demostración** | 6 cuentas para evaluar todos los roles y colas | `scripts/create_admin.py` |
| **Catálogo de Servicios** | 12 N1 y 46 N2 con SE.12 unificado e idempotencia | `GET /api/servicios`, `scripts/import_excel.py` |
| **Estructura Organizacional** | Cadena de 6 niveles sin registros huérfanos | `GET /api/organizacion`, `src/models.py` |
| **CMDB $\ge 5,000$ CIs** | Generación determinista con semilla y 3 niveles | `GET /api/cmdb/cis`, `scripts/generate_cmdb.py` |
| **Detección de Ciclos** | Validador DFS y análisis de impacto en cascada | `src/graph_service.py`, `GET /api/cmdb/cis/{id}/impacto` |
| **7 Procesos ITIL** | Ciclos de vida, aprobaciones CAB y matriz I0–I6 | `POST /api/tickets`, `docs/PROCESOS.md` |
| **Concurrencia en Colas** | Bloqueo pesimista `SELECT ... FOR UPDATE` (HTTP 409) | `POST /api/tickets/{id}/tomar` |
| **Harness Automatizado** | 18 de 18 escenarios de aceptación superados | `pytest tests/test_main.py -v` (18 passed) |
