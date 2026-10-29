# Guía Maestra de Defensa y Dominio Conceptual (`docs/GUIA_DEFENSA.md`)

**Asignatura:** Software Avanzado | USAC  
**Estudiante:** Andrés Calvo | **Carné:** 201712620  
**Catedrático:** Msc. Marco Tulio Aldana Prillwitz | **GitHub:** `maldanap-usac`  
**Proyecto:** Sistema Integral de Catálogo de Servicios TI, CMDB y Service Desk (ITIL)  

---

# PARTE 1: Conceptos y Términos Clave que Debes Dominar

## 1. Conceptos de ITIL, ITSM y Gestión de Servicios (Lecciones 22 y 25)

* **ITSM (IT Service Management):** Enfoque estratégico para diseñar, entregar, gestionar y mejorar la forma en que las tecnologías de la información se usan en una organización.
* **ITIL (Information Technology Infrastructure Library):** Marco de buenas prácticas estándar a nivel mundial para ITSM.
* **Catálogo de Servicios de TI:** Base de datos estructurada con información de todos los servicios tecnológicos en vivo que una organización ofrece a sus usuarios y al negocio.
* **Nivel 1 (N1) vs. Nivel 2 (N2):**
  * *Nivel 1:* Categoría o agrupación superior (ej. `SE.01` Servicios de Infraestructura).
  * *Nivel 2:* Servicio técnico operativo específico (ej. `SE.01.1` Provisión de Servidores Virtuales).
* **CMDB (Configuration Management Database - Lección 22):** Base de datos que almacena los registros de configuración durante todo su ciclo de vida y las **relaciones** entre ellos.
* **CI (Configuration Item / Elemento de Configuración):** Cualquier componente tecnológico que deba ser gestionado para entregar un servicio de TI (servidores, switches, bases de datos, aplicaciones, contratos).
* **SACM (Service Asset & Configuration Management):** Proceso ITIL cuyo objetivo es mantener información precisa sobre los activos y CIs necesarios para entregar servicios.
* **CMS vs. SKMS vs. DIKW (Lección 22):**
  * *CMS (Configuration Management System):* Conjunto de herramientas y bases de datos (incluida la CMDB) para administrar datos de configuración.
  * *SKMS (Service Knowledge Management System):* Sistema integral que contiene el conocimiento organizacional, documentación, lecciones aprendidas y FAQs.
  * *Pirámide DIKW:* Datos (*Data*) $\rightarrow$ Información (*Information*) $\rightarrow$ Conocimiento (*Knowledge*) $\rightarrow$ Sabiduría (*Wisdom*).
* **SPOC (Single Point of Contact - Lección 25):** Punto único de contacto. La Mesa de Ayuda (Service Desk) es el SPOC entre los usuarios y el departamento de TI.
* **Niveles de Escalamiento (Nivel 0 al 4 - Lección 25):**
  * *Nivel 0:* Autoservicio y Base de Conocimiento (FAQ). El usuario se atiende solo.
  * *Nivel 1:* Mesa de Ayuda (Help Desk). Primer contacto, triaje y solución de incidentes comunes.
  * *Nivel 2:* Soporte Técnico Especializado (redes, infraestructura, base de datos).
  * *Nivel 3:* Desarrollo / Arquitectura de Software y resolución de problemas de causa raíz.
  * *Nivel 4:* Proveedores externos y fabricantes de hardware/software bajo contrato (SLA externo).
* **SLA (Service Level Agreement):** Acuerdo de Nivel de Servicio que define tiempos límite de atención y solución comprometidos.
* **MTTA (Mean Time to Acknowledge):** Tiempo medio que tarda un agente en tomar/atender un ticket desde que se crea.
* **MTTR (Mean Time to Resolve):** Tiempo medio transcurrido hasta resolver y restituir el servicio.
* **Matriz I0–I6 de Incidentes (Lección 25):** Clasificación de severidad según duración e impacto:
  * $I0$: Incidente Mayor / Catástrofe ($SLA \le 30\text{ min}$).
  * $I1$: Crítico masivo ($SLA \le 2\text{ h}$).
  * $I2$: Alto degradado ($SLA \le 4\text{ h}$).
  * $I3$: Medio con alternativa ($SLA \le 8\text{ h}$).
  * $I4$: Medio interno ($SLA \le 24\text{ h}$).
  * $I5$: Menor ($SLA \le 48\text{ h}$).
  * $I6$: Consulta ($SLA \le 72\text{ h}$).
* **Eventos E0–E3 (Lección 25):**
  * $E0$: Informativo (operación normal).
  * $E1$: Advertencia (Warning, parámetro cercano al umbral).
  * $E2$: Excepción (falla con redundancia; detona incidente preventivo).
  * $E3$: Crítico (falla total sin redundancia; detona incidente mayor inmediato).
* **CAB (Change Advisory Board):** Comité de Aprobación de Cambios que autoriza o rechaza solicitudes de cambio (RFC).
* **KEDB (Known Error Database):** Base de datos de errores conocidos administrada por Gestión de Problemas.

---

## 2. Conceptos de Arquitectura, Concurrencia y Base de Datos

* **Idempotencia:** Propiedad de una operación de ejecutarse múltiples veces produciendo exactamente el mismo resultado sin duplicar ni corromper datos (ej. volver a importar el Excel o regenerar la CMDB).
* **Bloqueo Pesimista (`SELECT ... FOR UPDATE`):** Mecanismo de PostgreSQL que bloquea la fila del ticket en la base de datos durante una transacción. Si dos agentes hacen clic en "Tomar Ticket" al mismo milisegundo, la base de datos atiende al primero y al segundo le responde **`HTTP 409 Conflict`**, evitando *race conditions*.
* **Baja Lógica (*Soft Delete*):** En lugar de borrar registros físicamente con `DELETE`, se cambia una bandera (`activo = False`). Así se preserva el historial, integridad referencial y auditoría.
* **RBAC (Role-Based Access Control):** Control de acceso basado en roles (`administrador` vs. `consulta`). Validado **estrictamente en el servidor** (FastAPI), nunca solo ocultando botones en la pantalla.
* **Bcrypt con Sal (*Salt*):** Algoritmo criptográfico adaptativo para guardar contraseñas. Cada contraseña recibe una sal aleatoria que previene ataques de tablas arcoíris (*rainbow tables*).
* **DAG (Directed Acyclic Graph / Grafo Acíclico Dirigido):** Estructura matemática de nodos y flechas que no contiene ningún camino cerrado (sin ciclos). Es la regla que impide que el Servidor A dependa de B y B dependa de A.

---

## 3. Las 5 Disciplinas de Ingeniería con IA

1. **Context Engineering:** Saber qué documentos, reglas y límites suministrar al asistente (y cuáles omitir para no saturar su ventana de contexto). Incluye la regla de aislar datos externos no confiables.
2. **Prompt Engineering:** Diseñar instrucciones precisas bajo la estructura: *Objetivo + Contexto + Tarea + Restricciones + Salida Esperada + Criterio de Aceptación*.
3. **Harness Engineering:** Construir el "arnés" o entorno de pruebas automatizado que ejecuta, vigila y califica el código de forma determinista (Pytest, Docker, fixtures).
4. **Loop Engineering:** Ciclo de retroalimentación iterativo (*Plan ➔ Act ➔ Observe ➔ Evaluate ➔ Correct*) donde el asistente detecta un fallo en el arnés, analiza la causa raíz y lo corrige sin intervención humana.
5. **Graph Engineering:** Aplicar teoría de grafos (algoritmos DFS) para validar que no existan ciclos en la CMDB y calcular el impacto en cascada de fallas tecnológicas sobre los servicios de negocio.

---

# PARTE 2: Comparativa de Requisitos: Fase 1 vs. Fase 2

| Aspecto | Fase 1 (Parcial 2 - Base) | Fase 2 (Parcial 3 / Tarea Service Desk - Actual) |
|---|---|---|
| **Catálogo de Servicios** | 12 N1 y 46 N2 importados de `CatalogoServicios.xlsx`. Celdas combinadas con `ffill`, resolución canónica de `SE.12` y `NULL` en vacíos. | Se mantiene idéntico e intacto, pero ahora cada servicio se vincula con los CIs de la CMDB y recibe tickets. |
| **Organigrama** | Jerarquía de 6 niveles (`Empresa ➔ Área ➔ Depto ➔ Sección ➔ Puesto ➔ Usuario`). Asignación de responsable. | Base de usuarios y puestos expandida para soportar miembros de colas, agentes N1/N2 y aprobadores CAB. |
| **CMDB** | No existía. | **$\ge 5,000$ CIs generados sintéticamente** con semilla (`--seed 42`), 3 niveles de categorías (Lección 22) y relaciones topológicas sin ciclos. |
| **Grafos** | No existía. | **Graph Engineering:** Algoritmo DFS para rechazo de dependencias circulares y análisis de impacto en cascada hacia servicios N2. |
| **Tickets / Procesos** | No existía. | **7 Procesos ITIL completos** (Nuevos Servicios, Cambios, Incidentes I0–I6, Eventos E0–E3, Problemas, Accesos, Requisiciones). |
| **Colas & Concurrencia** | No existía. | 7 Colas especializadas con despacho determinista y **bloqueo pesimista `SELECT ... FOR UPDATE` (HTTP 409)** al tomar tickets. |
| **Portales Web** | Catálogo y Organigrama. | Portal de Autoservicio con **Base de Conocimiento (FAQ Nivel 0)**, Consola de Agente y Dashboard de SLAs (MTTA / MTTR). |
| **Harness de Pruebas** | P01 a P12 (12 pruebas). | **P01 a P18 (18 pruebas automatizadas de aceptación superadas al 100%)**. |

---

# PARTE 3: Mapa de Ubicación: ¿Dónde está cada cosa?

| Qué te pide el ingeniero | En qué archivo está | Qué función / línea revisar |
|---|---|---|
| **¿Dónde está el Harness de pruebas?** | `tests/test_main.py` | Contiene las 18 funciones `test_P01_...` a `test_P18_...`. |
| **¿Dónde ejecuto el Harness en vivo por API?** | `src/main.py` | Endpoint `@app.get("/harness/ejecutar")`. |
| **¿Dónde está la detección de ciclos de la CMDB?** | `src/graph_service.py` | Funciones `check_ci_relationship_cycle()` y `check_hierarchy_cycle()`. |
| **¿Dónde está el análisis de impacto en cascada?** | `src/graph_service.py` | Función `analyze_impact(ci_id)`. |
| **¿Dónde está el generador de los 5,000 CIs?** | `scripts/generate_cmdb.py` | Función `generate_cmdb_data(seed, target_count)`. |
| **¿Dónde está el control de concurrencia al tomar ticket?** | `src/main.py` | Endpoint `POST /api/tickets/{id}/tomar` (`with_for_update()`). |
| **¿Dónde están los modelos y tablas de BD?** | `src/models.py` | Clases `ConfigurationItem`, `Ticket`, `Cola`, `CIRelationship`, etc. |
| **¿Dónde está la importación del Excel?** | `scripts/import_excel.py` | Función `import_data()` con `ffill` y unificación canónica de `SE.12`. |
| **¿Dónde están las cuentas de prueba y colas demo?** | `scripts/create_admin.py` | Función `seed_demo_data()`. |
| **¿Dónde está la interfaz web SPA?** | `src/static/index.html` y `src/static/app.js` | Lógica de pestañas, modales, llamadas Fetch y renderizado dinámico. |
| **¿Dónde está la documentación de IA y Prompts?** | `docs/IA.md` | 8 prompts reales, 2 comparativas y 3 ciclos de Loop Engineering. |
| **¿Dónde está la máquina de estados de ITIL?** | `docs/PROCESOS.md` | Diagramas Mermaid de estados, reglas de negocio y cálculo de SLAs. |

---

# PARTE 4: Guía de Defensa ante el Catedrático (Cómo Responder)

### Pregunta 1: "¿Qué fue lo que hiciste tú en esta segunda fase?"
> **Tu respuesta sugerida:**  
> *"Ingeniero, en esta segunda fase evolucioné la plataforma desde el catálogo de servicios base hacia un **ecosistema integral de ITSM** que conecta la infraestructura tecnológica con la operación de TI.  
> Específicamente implementé cuatro pilares:  
> 1. Una **CMDB real de más de 5,000 elementos de configuración (CIs)** organizados en 3 niveles taxonómicos según la Lección 22, con relaciones técnicas y vinculación directa a los 46 servicios de catálogo.  
> 2. **Graph Engineering:** Algoritmos basados en DFS para impedir estrictamente dependencias circulares (garantizando un grafo acíclico DAG) y un motor de análisis de impacto en cascada.  
> 3. Un **Service Desk completo bajo ITIL** con los 7 procesos obligatorios, colas especializadas, niveles de escalamiento (Nivel 0 al 4), portal de autoservicio con FAQs y métricas de MTTA/MTTR.  
> 4. **Concurrencia atómica** al tomar tickets mediante bloqueo a nivel de fila (`SELECT ... FOR UPDATE` en PostgreSQL), retornando HTTP 409 ante colisiones.  
> Todo esto está validado de forma 100% automatizada con un **Harness de 18 pruebas de aceptación (P01 a P18)** que corre en Pytest con código de salida 0."*

---

### Pregunta 2: "¿Qué es el Harness y en dónde se encuentra?"
> **Tu respuesta sugerida:**  
> *"El **Harness** (o arnés de pruebas) es la infraestructura automatizada de software que valida objetiva e independientemente si el sistema cumple los contratos de aceptación, sin depender de pruebas manuales o inspección visual.  
> En el proyecto se encuentra en dos partes:  
> 1. **El código de pruebas formal:** Ubicado en `tests/test_main.py`, donde cada escenario (P01 al P18) es una función Pytest que evalúa códigos HTTP, restricciones en base de datos y lógica de negocio.  
> 2. **El ejecutor en vivo integrado en la API:** En `src/main.py` implementé el endpoint `GET /harness/ejecutar`, que ejecuta Pytest desde el backend y alimenta la pestaña **Harness P01–P18** de la interfaz web, permitiendo al evaluador certificar los 18 escenarios en tiempo real."*

---

### Pregunta 3: "¿Cómo resolviste la concurrencia cuando dos agentes toman el mismo ticket?"
> **Tu respuesta sugerida:**  
> *"Utilicé una estrategia de **bloqueo pesimista** (*Pessimistic Locking*) soportada de forma nativa por PostgreSQL.  
> En el endpoint `POST /api/tickets/{id}/tomar` ejecuto la consulta con `with_for_update()`. Esto hace que PostgreSQL adquiera un bloqueo exclusivo sobre la fila del ticket. Si un segundo agente presiona 'Tomar' al mismo tiempo, su hilo queda en espera en la base de datos hasta que la primera transacción termina. Cuando el segundo hilo entra, evalúa que el ticket ya tiene un `asignado_id` y que su estado cambió, abortando de inmediato y respondiendo con un **`HTTP 409 Conflict`** con el mensaje descriptivo correspondiente. El escenario automatizado **`P07`** comprueba exactamente esta colisión concurrente."*

---

### Pregunta 4: "¿Cómo garantizaste que la CMDB no tuviera ciclos infinitos?"
> **Tu respuesta sugerida:**  
> *"Apliqué **Graph Engineering** en `src/graph_service.py`. Distinguí las relaciones en dos tipos:  
> 1. Relaciones de dependencia técnica (`depende_de` y `alojado_en`), donde por definición física un componente no puede depender de sí mismo ni formar un ciclo. Ahí apliqué un recorrido en profundidad (**DFS**) que busca aristas hacia atrás (*back-edges*). Si detecta que al agregar una arista se visitaría un nodo que ya está en la pila activa de recursión, lanza una excepción que FastAPI traduce en un **`HTTP 400 Bad Request`**.  
> 2. Relaciones de red (`conectado_a`), donde sí se permiten topologías en anillo o malla redundante típicas de telecomunicaciones (Spanning Tree).  
> Además, implementé `analyze_impact(ci_id)` que recorre el grafo hacia arriba para calcular qué CIs y qué Servicios de Negocio Nivel 2 colapsarían si ese CI falla."*

---

### Pregunta 5: "¿Cómo evitaste que la IA alucinara o se dejara inyectar por los datos del Excel?"
> **Tu respuesta sugerida:**  
> *"Apliqué **Context Engineering** con una regla de aislamiento estricta documentada en `AGENTS.md`.  
> Los archivos de Excel (`CatalogoServicios.xlsx` y `CMDB.xlsx`) fueron catalogados como **datos pasivos no confiables**. Se instruyó al modelo que ningún texto, comentario o encabezado de celda debía interpretarse como instrucción o cambio de directiva.  
> Asimismo, toda la validación crítica (como la regla de que un solicitante no puede auto-aprobarse un acceso, o que un cambio no puede ejecutarse sin aprobación del CAB) reside en el servidor de FastAPI mediante Pydantic y restricciones relacionales en PostgreSQL, nunca en el cliente ni en suposiciones del prompt."*

---

### Comandos de Demostración Rápida por si te pide ejecutarlos en vivo:

```bash
# 1. Ejecutar las 18 pruebas de aceptación automatizadas
docker exec parcial_backend pytest tests/test_main.py -v

# 2. Re-generar la CMDB determinista con 5,000 CIs
docker exec -it parcial_backend python scripts/generate_cmdb.py --seed 42 --count 5000

# 3. Re-ejecutar la importación del Excel comprobando idempotencia
docker exec -it parcial_backend python scripts/import_excel.py
```
