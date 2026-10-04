# Resolución y Toma de Decisiones Técnicas

## 1. Arquitectura y Stack Tecnológico
Para abordar la solución de este parcial, opté por una arquitectura basada en contenedores (Docker) separando claramente la capa de persistencia (PostgreSQL) y la capa de lógica de negocio (FastAPI). La elección de FastAPI no fue fortuita: su validación nativa con Pydantic me permitió aislar e implementar reglas de negocio críticas (como la validación de rangos numéricos P09) directamente en la capa de esquemas, previniendo que datos sucios tocaran la base de datos.

## 2. Ingeniería de Datos y Calidad (El reto del Excel)
El archivo `CatalogoServicios.xlsx` presentaba desafíos intencionales de limpieza, destacando las celdas combinadas y el conflicto de nombres para el código `SE.12`. 
Decidí prescindir de manipulaciones manuales en Excel y construí un script de ingesta robusto (`import_excel.py`) apoyándome en la librería `pandas`.
*   **Decisión Técnica 1:** Utilicé el método `ffill()` (forward fill) de Pandas para propagar el contexto de las categorías padre (Nivel 1) hacia los servicios hijos, resolviendo programáticamente la pérdida de datos de las celdas combinadas.
*   **Decisión Técnica 2:** Para el código anómalo `SE.12`, codifiqué una regla de negocio explícita que intercepta y unifica los registros bajo el nombre canónico *"Suministrar Analítica y Tableros de Control"*, emitiendo un log de trazabilidad por consola sin abortar la ejecución.

## 3. Seguridad y Criptografía
Cumpliendo la directiva de no usar proveedores externos como Auth0, diseñé un esquema de autenticación local con JWT. 
Durante la implementación, la librería estándar `passlib` arrojó un conflicto con versiones modernas de `bcrypt` (un bug reportado y documentado en la comunidad). En lugar de aplicar un *downgrade* de la librería (lo cual considero riesgoso para la seguridad en entornos reales), decidí ser proactivo y reescribir el módulo `auth.py` para utilizar directamente `bcrypt` puro, garantizando la generación criptográfica de "sal" (*salt*) y un hashing moderno.

## 4. Context & Harness Engineering
*   **Context Engineering:** Inyecté instrucciones específicas en el archivo `AGENTS.md` para proteger el entorno contra *Prompt Injection*. Quedó estrictamente delimitado que el archivo Excel de servicios debía ser tratado como "Data" pasiva, blindando al LLM contra cualquier ejecución de comandos oculta en las celdas.
*   **Harness Engineering:** Ante los múltiples requisitos funcionales, construí una suite automatizada de pruebas unitarias y de integración mediante `pytest`. En lugar de probar a mano, el script `test_main.py` levanta un `TestClient` simulando ataques e ingresos inválidos (P01, P02, P03) y validaciones de esquema (P05, P09), comprobando la resiliencia de la API en segundos.

---

## Matriz de Cumplimiento Normativo

| Req | Descripción | Estado | Justificación / Implementación Técnica |
|-----|-------------|--------|-----------------------------|
| P01 | Evitar accesos no autorizados | Completado | Endpoints protegidos; validación manual de contraseña encriptada (bcrypt) y emisión de token JWT. Fallo simulado en pytest. |
| P02 | Control de usuarios inactivos | Completado | El modelo `Usuario` incluye atributo `activo`. El middleware de FastAPI rechaza la conexión con HTTP 403. |
| P03 | Sólo administrador crea servicios | Completado | Implementación de dependencia `admin_required` que desencripta el JWT y verifica el claim de rol. |
| P04 | Jerarquía organizacional base | Completado | Desarrollé `crear_admin.py` que inyecta programáticamente toda la cadena: Empresa->Área->Depto->Sección->Puesto->Usuario. |
| P05 | Código de servicio único | Completado | Restricción `unique=True` a nivel SQL; validación preventiva en el controlador (`HTTP 400`). |
| P09 | Regla Mínimo/Máximo | Completado | Decorador `@validator` en Pydantic (`schemas.py`) que intercepta valores donde Mínimo > Máximo antes de llegar a la lógica. |
| P10 | Búsqueda y Filtros | Completado | Endpoint `GET /servicios/` incluye parámetro `q` procesado mediante un `ilike` seguro en SQLAlchemy. |
| P11/P12 | Manejo de nulos / Trazabilidad | Completado | El script `import_excel.py` mantiene los campos vacíos en estado `null` sin falsear información, e imprime reportes en la consola de Docker. |
