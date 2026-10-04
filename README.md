# Sistema de Gestión del Catálogo de Servicios de TI

## Datos de Entrega
- **Nombre:** Andrés Calvo
- **Carné:** 201712620
- **URL del Repositorio:** https://github.com/AndresCalvo98/parcial-catalogo-servicios-201712620
- **Rama:** master
- **Etiqueta de Entrega:** parcial-v2.0

Este repositorio contiene la solución completa al Parcial Práctico de Software Avanzado. Se implementó una aplicación web utilizando FastAPI, PostgreSQL y Docker, con soporte explícito y documentado para Context, Prompt y Harness Engineering.

## 1. Requisitos Previos
- Docker y Docker Compose instalados.
- El archivo de datos original (`CatalogoServicios.xlsx`) ya se encuentra en la carpeta `data/`.

## 2. Configuración Inicial
1. Clona el repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd parcial-catalogo-servicios-201712620
   ```
2. Configura las variables de entorno copiando el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```
   *(Nota: El archivo `.env.example` ya contiene credenciales base para que la aplicación conecte con PostgreSQL inmediatamente sin configuración adicional).*

## 3. Levantamiento del Entorno (Docker)
Para levantar la base de datos (PostgreSQL) y el backend (FastAPI), ejecuta:
```bash
docker compose up --build -d
```
Espera unos 15-20 segundos para que PostgreSQL inicialice y el backend termine de instalar sus dependencias.

Para revisar los logs del servidor y confirmar que todo está en orden:
```bash
docker compose logs -f backend
```

## 4. Inicialización y Migración de Datos

Toda la interacción con el sistema y los scripts se realiza a través del contenedor de Docker. Ejecuta los siguientes comandos en orden para hidratar la base de datos:

**Paso 1: Crear las tablas en la base de datos**
```bash
docker exec parcial_backend python scripts/init_db.py
```

**Paso 2: Importar el Catálogo desde el Excel**
Este script aplica limpieza de celdas combinadas y resuelve conflictos como el del código "SE.12" utilizando `pandas`.
```bash
docker exec parcial_backend python scripts/import_excel.py
```

**Paso 3: Crear Jerarquía y Usuarios de Evaluación**
Esto inyecta programáticamente la jerarquía organizacional obligatoria y genera los usuarios para la demostración.
```bash
docker exec parcial_backend python scripts/create_admin.py
```

## 5. Acceso y Verificación (Credenciales de Evaluación)

- **Swagger UI:** Ingresa a http://localhost:8000/docs
- **Usuario Administrador:** `admin@demo.com`
- **Contraseña Administrador:** `admin123`
- **Usuario Consulta:** `normal@demo.com`
- **Contraseña Consulta:** `clave`

*(Puedes iniciar sesión directamente usando el botón "Authorize" de Swagger UI).*

## 6. Pruebas Automatizadas (Harness Engineering)
Para verificar los escenarios P01, P02, P03, P05 y P09 automatizados (inicio de sesión inválido, escalación de roles, validaciones min/max, etc.), ejecuta el siguiente comando:
```bash
docker exec parcial_backend pytest tests/test_main.py -v
```
Verás la salida en verde demostrando que las reglas de negocio detienen accesos no autorizados y previenen la corrupción de datos.

## 7. Detener y Reiniciar el Sistema
Para apagar los contenedores conservando la información (el volumen de la base de datos persiste):
```bash
docker compose down
```

Para reiniciar desde cero (destrucción intencionada de datos para una re-evaluación limpia):
```bash
docker compose down -v
```

## 8. Documentación Estructural del Proyecto
De acuerdo a los requisitos del examen, revisa la siguiente documentación detallada:
- [AGENTS.md](AGENTS.md): Reglas de mitigación y Context Engineering.
- [RESOLUCION.md](docs/RESOLUCION.md): Matriz de cumplimiento, diagrama, justificaciones de diseño, y detalle del mapeo de datos.
- [Prompts Utilizados](docs/prompts/prompts_utilizados.md): Iteración de Prompts (Prompt Engineering).
- [Evidencias de Pruebas](docs/evidencias/reporte_pytest.txt): Salida de resultados de la suite de Harness Engineering.
