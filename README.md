# Sistema de Gestión del Catálogo de Servicios de TI

> **Asignatura:** Software Avanzado | USAC  
> **Estudiante:** Andrés Calvo — Carné `201712620`  
> **Repositorio:** `https://github.com/AndresCalvo98/parcial-catalogo-servicios-201712620`  
> **Etiqueta de Entrega:** `parcial-v2.0`

---

## Descripción General

Aplicación web completa y API RESTful para gestionar el catálogo de servicios de TI de una organización, construida con:

- **Backend:** FastAPI + SQLAlchemy (Python 3.11)
- **Base de datos:** PostgreSQL 15
- **Contenedores:** Docker + Docker Compose
- **Frontend:** HTML5 + CSS3 + JavaScript Vanilla (Single-Page Application)
- **Autenticación:** JWT local con hash `bcrypt` (OAuth2 Password Flow)

La solución aplica y demuestra **Context Engineering**, **Prompt Engineering** y **Harness Engineering** según los requisitos del parcial.

---

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

| Herramienta | Versión mínima | Verificación |
|---|---|---|
| Docker Desktop | 24.x | `docker --version` |
| Docker Compose | 2.x (incluido en Docker Desktop) | `docker compose version` |

> ⚠ Los puertos **`8000`** y **`5432`** deben estar libres en tu máquina local.

---

## 1. Clonar el Repositorio

```bash
git clone https://github.com/AndresCalvo98/parcial-catalogo-servicios-201712620.git
cd parcial-catalogo-servicios-201712620
```

---

## 2. Configurar las Variables de Entorno

El archivo `.env` contiene las credenciales de la base de datos y la clave secreta JWT. Ya viene pre-configurado, pero si necesitas generarlo desde la plantilla:

```bash
# Solo si no existe el archivo .env:
cp .env.example .env
```

> ℹ El `.env` de este repositorio ya tiene valores funcionales listos para evaluación. **No es necesario editarlo**.

---

## 3. Construir y Levantar los Contenedores

```bash
docker compose up --build -d
```

Este comando:
1. Construye la imagen del backend con el `Dockerfile`
2. Levanta el contenedor `parcial_db` (PostgreSQL)
3. Espera a que la DB esté lista (healthcheck integrado)
4. Levanta el contenedor `parcial_backend` (FastAPI)

Para verificar que ambos contenedores están corriendo:

```bash
docker compose ps
```

Para ver los logs del backend en tiempo real:

```bash
docker compose logs -f backend
```

> ✅ Cuando veas `Application startup complete.` en los logs, el sistema está listo.

---

## 4. Inicializar la Base de Datos (Opcional / Verificación)

> 💡 **Nota de Arquitectura (Zero-Config):** El backend cuenta con un gestor `lifespan` que ejecuta automáticamente la verificación de tablas, importación de Excel y siembra de usuarios en el primer arranque. Si deseas comprobar el funcionamiento paso a paso o forzar la recarga manual, ejecuta los 3 comandos siguientes (todos son 100% **idempotentes**):

### Paso 1 — Crear tablas del modelo relacional

```bash
docker exec parcial_backend python scripts/init_db.py
```

**Qué hace:** Crea todas las tablas en PostgreSQL (`empresas`, `areas`, `departamentos`, `secciones`, `puestos`, `usuarios`, `servicios_nivel1`, `servicios_nivel2`, catálogos auxiliares).

---

### Paso 2 — Importar catálogo desde Excel

```bash
docker exec parcial_backend python scripts/import_excel.py
```

**Qué hace:**
- Lee el archivo `data/CatalogoServicios.xlsx`
- Aplica `ffill` (Forward Fill) para resolver celdas combinadas
- Resuelve el conflicto canónico del código `SE.12`
- Normaliza catálogos de Clase, Criticidad y Tipo
- Carga 12 servicios Nivel 1 y 46 servicios Nivel 2 con **idempotencia** (es re-ejecutable sin duplicados)

---

### Paso 3 — Crear jerarquía organizacional y usuarios de demostración

```bash
docker exec parcial_backend python scripts/create_admin.py
```

**Qué hace:**
- Crea la jerarquía: `USAC → DTI → Departamento Desarrollo → 2 Secciones → 2 Puestos`
- Registra los 2 usuarios de evaluación (admin y consulta)
- Vincula 3 asignaciones válidas de servicios a secciones y usuarios

---

## 5. Acceder al Sistema

Una vez completados los pasos anteriores:

| Recurso | URL |
|---|---|
| 🌐 **Aplicación Web (Frontend)** | [http://localhost:8000](http://localhost:8000) |
| 📘 **Documentación API (Swagger UI)** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| 🔗 **API REST alternativa (ReDoc)** | [http://localhost:8000/redoc](http://localhost:8000/redoc) |

### Credenciales de Evaluación

| Rol | Correo | Contraseña | Permisos |
|---|---|---|---|
| **Administrador** | `admin@demo.com` | `admin123` | CRUD completo, gestión de usuarios, bajas lógicas |
| **Consulta** | `normal@demo.com` | `clave` | Solo lectura (GET). Operaciones de escritura rechazadas con HTTP 403 |

> El frontend incluye botones de **acceso rápido** para cada rol en el modal de inicio de sesión.

---

## 6. Ejecutar Pruebas Automatizadas (Harness Engineering)

La suite de pruebas automatizadas valida los **12 escenarios de aceptación (P01 a P12)**:

```bash
docker exec parcial_backend pytest tests/test_main.py -v
```

**Resultado esperado:** Todos los tests deben mostrar `PASSED` en verde (12 passed).

Para ejecutar un test específico:

```bash
docker exec parcial_backend pytest tests/test_main.py::test_P01_inicio_sesion_valido_e_invalido -v
```

---

## 7. Gestión del Entorno

### Detener los contenedores (preservando datos)

```bash
docker compose down
```

Al volver a levantarlos con `docker compose up -d`, todos los datos persisten en el volumen `db_data`.

### Reinicio completo (limpieza total para re-evaluación)

```bash
docker compose down -v
```

Este comando elimina los contenedores **y el volumen** de datos. Luego debes repetir el paso 4 completo.

### Reconstruir la imagen después de cambios en el código

```bash
docker compose up --build -d
```

---

## 8. Estructura del Proyecto

```
parcial-catalogo-servicios-201712620/
├── src/
│   ├── main.py         # API REST FastAPI — todos los endpoints
│   ├── models.py       # Modelos SQLAlchemy (ORM)
│   ├── schemas.py      # Esquemas Pydantic (validación)
│   ├── auth.py         # Autenticación JWT + bcrypt
│   ├── database.py     # Conexión PostgreSQL (engine, sesiones)
│   └── static/
│       ├── index.html  # SPA — Interfaz de usuario
│       ├── style.css   # Sistema de diseño premium
│       └── app.js      # Lógica de cliente (sin frameworks)
├── scripts/
│   ├── init_db.py      # Creador de tablas (Paso 1)
│   ├── import_excel.py # ETL desde Excel (Paso 2)
│   └── create_admin.py # Seeder org. y usuarios (Paso 3)
├── tests/
│   └── test_main.py    # Suite pytest (P01–P12)
├── data/
│   └── CatalogoServicios.xlsx  # Archivo fuente original preservado
├── docs/
│   ├── RESOLUCION.md   # Informe técnico completo (ER, decisiones, AI)
│   ├── prompts/        # Fichas de prompts y mejoras iterativas
│   ├── contexto/       # Documentación de contexto versionada
│   └── evidencias/     # Capturas de pantalla y evidencias
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .env                # Variables de entorno (NO subir a GitHub real)
├── .gitignore
├── AGENTS.md           # Directivas para IA y registro de actualizaciones
└── README.md           # Este archivo
```

---

## 9. Documentación Técnica

| Documento | Ubicación | Contenido |
|---|---|---|
| **AGENTS.md** | Raíz del proyecto | Directivas operativas para IA, protección anti-inyección, registro de 2 actualizaciones versionadas |
| **RESOLUCION.md** | `docs/RESOLUCION.md` | Informe técnico: Diagrama ER en Mermaid, mapeo Excel, matriz de cumplimiento P01–P12, reflexión sobre IA |
| **prompts_utilizados.md** | `docs/prompts/` | Fichas técnicas de ≥5 prompts y registro de ≥2 iteraciones empíricas de mejora |
| **docs/contexto/** | `docs/contexto/` | Documentación de contexto suministrada en 3 fases de desarrollo |
