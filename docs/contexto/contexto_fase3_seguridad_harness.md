# Contexto Fase 3: Actualización 2 - Seguridad Criptográfica y Reglas de Negocio P11

**Fecha de Actualización:** 03 de Octubre 2026  
**Motivación del Cambio:** Conflicto de librerías criptográficas e integración de validación organizacional P11.  
**Documentos suministrados al asistente:** Trazas de error de Docker, especificación de requisitos funcionales P01 a P12.

---

## 1. Cambio de Decisión Criptográfica (Passlib vs Bcrypt Nativo)
* **Incidencia:** La librería `passlib[bcrypt]` presentó un error de compatibilidad (`ValueError: password cannot be longer than 72 bytes`) al interactuar con las versiones recientes de la librería `bcrypt` de C-Python.
* **Resolución y Actualización de Contexto:** Se actualizó el contexto técnico del asistente ordenando abandonar `passlib` y utilizar la librería `bcrypt` de forma directa con sal (*salt*) criptográfica segura (`bcrypt.gensalt()` y `bcrypt.hashpw()`).

## 2. Refuerzo de la Regla de Asignación Organizacional (P11)
* **Regla:** Ningún servicio puede tener asignado un usuario responsable que no pertenezca a la misma sección organizacional que administra el servicio.
* **Resolución:** El contexto instruye a la capa de esquemas y controladores de FastAPI a verificar la pertenencia del usuario al puesto y a la sección antes de persistir cualquier cambio (`HTTP 400`).
