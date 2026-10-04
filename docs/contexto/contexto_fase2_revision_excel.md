# Contexto Fase 2: Actualización 1 - Hallazgos en Ingesta de Excel

**Fecha de Actualización:** 02 de Octubre 2026  
**Motivación del Cambio:** Hallazgos anómalos durante el análisis técnico preliminar del archivo `CatalogoServicios.xlsx`.  
**Documentos suministrados al asistente:** `CatalogoServicios.xlsx`, script de inspección con Pandas.

---

## 1. Hallazgos Críticos Identificados
1. **Celdas Combinadas en Nivel 1 (Columnas A y B):**
   * El Excel combina celdas verticalmente para agrupar servicios de Nivel 2.
   * La lectura directa en Python deja valores `NaN` en filas intermedias.
   * *Decisión:* Inyectar en el contexto la directiva de aplicar `forward fill (ffill())` en las columnas `COD_N1` y `NOMBRE_N1` antes de filtrar servicios hijos.

2. **Conflicto del Código SE.12 (Filas 99 y 100):**
   * El código `SE.12` aparece dos veces con nombres contradictorios: *"Suministrar Analitica"* y *"Mantener Tableros de Control"*.
   * *Decisión:* Establecer como política de negocio el nombre canónico unificado *"Suministrar Analítica y Tableros de Control"*, registrando la incidencia en el log de observaciones para mantener idempotencia y unicidad.

3. **Valores Ausentes en Filas 99 a 101:**
   * Múltiples servicios carecen de clase, criticidad, tipo o métrica.
   * *Decisión:* Prohibir expresamente la inferencia o invención de datos. Los campos deben conservarse como `null` en base de datos.
