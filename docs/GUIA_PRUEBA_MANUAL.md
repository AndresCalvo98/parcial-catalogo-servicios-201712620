# Guía Paso a Paso de Prueba Manual en Frontend

> **Asignatura:** Software Avanzado — USAC  
> **Estudiante:** Andrés Calvo | Carné `201712620`  
> **Sistema:** Catálogo de Servicios de TI  
> **URL Local:** [http://localhost:8000](http://localhost:8000)

---

Esta guía está diseñada para que realices una **demostración manual completa frente al catedrático**, mostrando cómo cada requerimiento del enunciado (P01 a P12) se refleja y valida visualmente en la interfaz gráfica.

---

## 1. Demostración de Autenticación y Sesiones (P01 y P02)

### Caso 1.1 — Intento de acceso fallido (P01)
1. Abre [http://localhost:8000](http://localhost:8000) en el navegador.
2. Si no has iniciado sesión, haz clic en el botón **"Iniciar Sesión"** en la barra lateral izquierda.
3. En el formulario, escribe un correo cualquiera o contraseña errónea (ej. `admin@demo.com` y `password_falsa`).
4. Haz clic en **"Iniciar Sesión"**.
5. **Resultado esperado:** Aparece una alerta roja debajo del formulario indicando:  
   `Correo o contraseña incorrectos (P01)`.

### Caso 1.2 — Inicio de sesión válido con Acceso Rápido (P01)
1. En el mismo modal de inicio de sesión, observa la sección inferior llamada *"Acceso rápido de evaluación"*.
2. Haz clic en el botón azul **"Administrador"**.
3. El sistema autocompleta las credenciales (`admin@demo.com` / `admin123`) e inicia sesión automáticamente.
4. **Resultado esperado:**
   - El modal se cierra.
   - En la esquina inferior izquierda aparece tu perfil con avatar **A**, nombre `Administrador Demo` y una etiqueta verde `administrador`.
   - Se habilitan los módulos administrativos (botón `+ Nuevo Servicio`, pestaña `Usuarios`, botones de edición y eliminación).

### Caso 1.3 — Cierre de sesión (Logout - P02)
1. Haz clic en el botón rojo de salida (ícono de puerta) junto a tu nombre de usuario en la barra lateral.
2. **Resultado esperado:**
   - La sesión finaliza inmediatamente.
   - La barra lateral vuelve al estado *"Iniciar Sesión"*.
   - Los botones de edición y borrado desaparecen de la tabla.

---

## 2. Demostración de Control de Acceso por Roles / RBAC (P03)

### Caso 2.1 — Iniciar sesión con rol "Consulta" (Solo Lectura)
1. Haz clic en **"Iniciar Sesión"**.
2. Haz clic en el botón gris **"Solo Consulta"** (`normal@demo.com` / `clave`).
3. **Resultado esperado:**
   - El perfil muestra la etiqueta celeste `consulta`.
   - El botón verde `+ Nuevo Servicio` está oculto.
   - La pestaña `Usuarios` en el menú lateral está oculta.
   - En la columna "Acciones" de la tabla de servicios solo aparece el botón de ver ficha (`👁️`), **sin opciones de editar ni eliminar**.
   - Esto demuestra que el rol consulta solo tiene privilegios de lectura (GET).

---

## 3. Demostración de Catálogo, Búsqueda y Filtros (P06, P08 y P10)

*(Inicia sesión nuevamente como Administrador para esta sección).*

### Caso 3.1 — Verificación de los 46 servicios físicos (P06)
1. En la pestaña **"Catálogo de Servicios"**, observa las 4 tarjetas de métricas superiores:
   - **Total Servicios:** `46` (los 46 servicios físicos del Excel `CatalogoServicios.xlsx`).
   - **Activos:** Cantidad con estado `S`.
   - **Inactivos:** Servicios con baja lógica `N` o nulos.
   - **Categorías N1:** `12` categorías principales.

### Caso 3.2 — Búsqueda en tiempo real (P10)
1. En el campo de búsqueda (arriba a la izquierda de la tabla), escribe: `SE.01`.
2. **Resultado esperado:** La tabla filtra instantáneamente mostrando únicamente los servicios del código `SE.01` (`SE.01.01`, `SE.01.02`, etc.).
3. Borra el texto de búsqueda: la tabla restaura los 46 servicios inmediatamente.

### Caso 3.3 — Filtros combinados multi-criterio (P10)
1. Despliega el filtro **"Criticidad"** y selecciona `CRITICA` o `ALTA`.
2. Despliega el filtro **"Clase"** y selecciona `RECURRENTE`.
3. Despliega el filtro **"Estado"** y selecciona `✅ S — Activo`.
4. **Resultado esperado:** La tabla muestra solo los servicios que cumplen todos los criterios seleccionados simultáneamente.
5. Haz clic en el botón **"Limpiar Filtros"** para restablecer la vista.

### Caso 3.4 — Ver Ficha Técnica y Exportar JSON (P08)
1. En cualquier fila, haz clic en el ícono del ojo (`👁️`).
2. **Resultado esperado:** Se abre un modal detallado con la ficha técnica:
   - Código único y categoría padre Nivel 1.
   - Badges de Clase, Criticidad y Tipo.
   - Métrica y umbrales (Mínimo / Máximo).
   - Sección responsable asignada.
   - Descripción completa del servicio.
3. Haz clic en el botón **"Exportar JSON"** para demostrar que la ficha se puede descargar como archivo JSON estructurado.

---

## 4. Demostración de Validación de Umbrales Mínimo ≤ Máximo (P09)

1. En la parte superior derecha de la tabla, haz clic en **`+ Nuevo Servicio`**.
2. Llena los campos requeridos:
   - **Código Único:** `SE.DEMO.99`
   - **Servicio Padre:** Selecciona cualquiera (ej. `SE.01 - Gestionar Accesos...`).
   - **Nombre:** `Servicio de Prueba Umbrales`.
3. En la sección de umbrales:
   - **Umbral Mínimo:** Ingresa `500`.
   - **Umbral Máximo:** Ingresa `100`.
4. Haz clic en **"Guardar Servicio"**.
5. **Resultado esperado:** El formulario no se envía y aparece una alerta roja clara:  
   `⚠ Error P09: El umbral mínimo no puede ser mayor que el máximo.`
6. Corrige los valores: Mínimo `10` y Máximo `100`. La alerta desaparece al guardar.

---

## 5. Demostración de Regla de Negocio: Sección vs Responsable (P11)

1. Abre el modal de **`+ Nuevo Servicio`** (o edita uno existente con el lápiz `✏️`).
2. En el campo **"Sección Responsable"**, selecciona `Sección de Arquitectura y Backend`.
3. Abre el menú desplegable de **"Usuario Responsable"**.
4. **Resultado esperado:** El combo solo lista a los usuarios que pertenecen a esa sección (`Líder Técnico de Software - Andres Calvo`), filtrando automáticamente a los demás empleados.
5. Si intentas forzar por API un usuario de otra sección, el backend rechaza la petición con código `HTTP 400`:  
   `Operación rechazada: El usuario responsable no pertenece a la sección del servicio (P11)`.

---

## 6. Demostración de Bajas Lógicas (P10)

1. En la tabla de servicios, busca el servicio de prueba que creaste o uno con código de prueba.
2. Haz clic en el ícono de la papelera roja (`🗑️`).
3. El navegador mostrará un cuadro de confirmación:  
   *`¿Confirmas la baja lógica de este servicio? El registro se desactivará pero no se eliminará de la base de datos.`*
4. Haz clic en **Aceptar**.
5. **Resultado esperado:**
   - Aparece una notificación Toast verde en la esquina superior derecha:  
     `Servicio dado de baja lógicamente ✓`.
   - El registro cambia su estado a `❌ N` (inactivo), conservando su histórico en PostgreSQL sin eliminar la fila física (`DELETE`).

---

## 7. Demostración de Estructura Organizacional Jerárquica (P04)

1. En el menú lateral, haz clic en la pestaña **"Estructura Org."**.
2. **Resultado esperado:** Se despliega el árbol visual multinivel completo:
   - 🏢 **Empresa:** `Universidad de San Carlos de Guatemala (USAC)`
   - 📁 **Área:** `Dirección General de Tecnología (DTI)`
   - 🏬 **Departamento:** `Departamento de Desarrollo e Innovación (DDEV)`
   - 📑 **Secciones:**
     - `Sección de Arquitectura y Backend (SEC-BND)`
     - `Sección de Operaciones e Infraestructura (SEC-OPS)`
   - 💼 **Puestos:** `Líder Técnico de Software` y `Especialista en Infraestructura`
   - 👤 **Usuarios:** Muestra a cada usuario asignado con su correo, rol y estado.
3. Haz clic en el botón **"Actualizar"** para refrescar la jerarquía en vivo.

---

## 8. Demostración de Gestión de Usuarios (P04)

1. En el menú lateral, haz clic en la pestaña **"Usuarios"**.
2. Se muestra la tabla con todos los usuarios registrados, sus correos, roles (`administrador` / `consulta`), puesto asignado y estado (`Activo` / `Inactivo`).
3. Haz clic en el botón verde **`+ Nuevo Usuario`**:
   - Permite crear una nueva cuenta definiendo nombre, correo, contraseña, rol y asignándole un puesto de la estructura organizacional.

---

## 9. Demostración de Harness Engineering en Vivo (P01 a P12)

1. En el menú lateral, haz clic en la pestaña **"Reporte de Calidad"**.
2. En la parte superior verás las tarjetas con los 4 indicadores de calidad del ETL:
   - `12` Códigos N1
   - `46` Servicios N2
   - `100%` Idempotencia
   - `3` Conflictos resueltos (`SE.12`, celdas combinadas y atributos ausentes)
3. En la sección **"Harness Engineering — Suite de Pruebas de Aceptación (P01–P12)"**:
4. Haz clic en el botón azul: **`▶ Ejecutar Suite en Vivo`**.
5. **Resultado esperado:**
   - El botón muestra un indicador de carga (`Ejecutando Pytest…`).
   - El backend ejecuta la suite completa de 12 pruebas en tiempo real contra PostgreSQL.
   - En ~5 segundos aparece un banner verde certificado:  
     **`12 / 12 Pruebas de Aceptación Superadas (100% Cobertura)`** indicando el tiempo de ejecución (ej. `4.8s`) y `0 errores`.
   - La tabla despliega cada una de las 12 reglas con su badge verde `✓ PASSED`, su componente y la descripción técnica de lo que se comprobó.
6. En la parte inferior de esa sección, muéstrale al ingeniero el comando CLI equivalente:
   ```bash
   docker exec parcial_backend pytest tests/test_main.py -v
   ```

---

## Resumen de Credenciales para Demostración

| Rol | Correo | Contraseña | Atajo Frontend |
|---|---|---|---|
| **Administrador (CRUD Total)** | `admin@demo.com` | `admin123` | Botón azul *"Administrador"* |
| **Consulta (Solo Lectura)** | `normal@demo.com` | `clave` | Botón gris *"Solo Consulta"* |

¡Siguiendo estos pasos en este orden, demostrarás el 100% de la funcionalidad del parcial de forma fluida, profesional y contundente!
