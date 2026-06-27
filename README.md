# Sistema de Gestión de Turnos Médicos (SGTM)

**Asignatura:** Diseño de Software — Informática 2026  
**Repositorio:** [emelgarejo2024/SGTM-Django](https://github.com/emelgarejo2024/SGTM-Django)  
**Stack principal:** Django 6 · PostgreSQL 15 · Python 3.12

---

## Tabla de Contenidos

1. [Descripción del Sistema](#1-descripción-del-sistema)
2. [Arquitectura](#2-arquitectura)
3. [Tecnologías y Dependencias](#3-tecnologías-y-dependencias)
4. [Requisitos Previos](#4-requisitos-previos)
5. [Instalación y Configuración](#5-instalación-y-configuración)
6. [Variables de Entorno](#6-variables-de-entorno)
7. [Comandos del Makefile](#7-comandos-del-makefile)
8. [Testing y Cobertura](#8-testing-y-cobertura)
9. [Pipeline de Integración Continua](#9-pipeline-de-integración-continua)
10. [Estructura del Proyecto](#10-estructura-del-proyecto)
11. [Reglas de Negocio Implementadas](#11-reglas-de-negocio-implementadas)
12. [Equipo de Desarrollo](#12-equipo-de-desarrollo)

---

## 1. Descripción del Sistema

El SGTM es una plataforma web centralizada para la administración de citas médicas entre pacientes y profesionales de la salud. El sistema digitaliza y automatiza el proceso de agendamiento, eliminando los errores asociados a la gestión manual y garantizando la consistencia de datos mediante reglas de negocio formales.

**Funcionalidades principales:**

- Reserva, cancelación y reagendamiento autónomo de turnos por parte del paciente.
- Gestión de disponibilidad horaria por parte del profesional médico.
- Registro de asistencia presencial mediante Check-in.
- Auditoría automática de todas las operaciones del sistema.
- Penalización automática ante inasistencias reiteradas (No-shows).

---

## 2. Arquitectura

El proyecto aplica una **Arquitectura por Capas** complementada con dos patrones de diseño clásicos de la literatura de ingeniería de software.

### 2.1 Patrón Facade (`services.py`)

La capa de servicios encapsula la complejidad de la lógica de negocio, exponiendo una interfaz simplificada hacia las vistas. Las vistas no tienen conocimiento directo de cómo se valida ni se persiste una reserva.

```
Capa de Presentación  →  views.py
Capa de Servicios     →  services.py   (Facade: lógica de negocio + atomicidad)
Capa de Datos         →  models.py     (Validaciones en clean() + CheckConstraints)
```

### 2.2 Patrón Observer (`signals.py`)

Django Signals actúa como bus de eventos interno. Al crearse o modificarse una reserva, el sistema dispara automáticamente el registro de auditoría sin acoplar esta responsabilidad al flujo principal de la transacción.

```
Reserva.save()  -->  Signal post_save  -->  Registro de auditoría
```

### 2.3 Atomicidad y Control de Concurrencia

La operación de reserva utiliza `select_for_update()` dentro de `transaction.atomic()` para garantizar que múltiples solicitudes simultáneas sobre el mismo bloque horario no produzcan estados inconsistentes (doble booking). Esta implementación satisface directamente la regla de negocio BR-13 del SRS.

---

## 3. Tecnologías y Dependencias

| Componente           | Herramienta     | Versión |
| -------------------- | --------------- | ------- |
| Framework backend    | Django          | 6.0.5   |
| Base de datos        | PostgreSQL      | 15+     |
| Driver de base datos | psycopg2-binary | 2.9.12  |
| Framework de testing | pytest          | 9.1.1   |
| Plugin Django pytest | pytest-django   | 4.12.0  |
| Cobertura de código  | pytest-cov      | 7.1.0   |
| Análisis estático    | Flake8          | 7.3.0   |
| Formateo de código   | Black           | 26.5.1  |
| Variables de entorno | python-dotenv   | 1.2.2   |
| Calidad de código    | SonarQube (UCT) | —       |
| CI/CD                | GitHub Actions  | —       |

---

## 4. Requisitos Previos

- Python 3.12 o superior
- PostgreSQL 15 o superior (instancia activa y accesible)
- Git
- `make` (opcional, para usar los comandos centralizados del Makefile)

---

## 5. Instalación y Configuración

**Paso 1 — Clonar el repositorio**

```bash
git clone https://github.com/emelgarejo2024/SGTM-Django.git
cd SGTM-Django/sgtm_proyecto
```

**Paso 2 — Crear y activar el entorno virtual**

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

**Paso 3 — Instalar dependencias**

```bash
make install
```

**Paso 4 — Configurar variables de entorno**

```bash
cp .env.example .env
# Editar .env con las credenciales del entorno local
```

**Paso 5 — Crear la base de datos en PostgreSQL**

```sql
CREATE DATABASE sgtm_db;
CREATE USER sgtm_admin WITH PASSWORD 'contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE sgtm_db TO sgtm_admin;
```

**Paso 6 — Aplicar migraciones**

```bash
python manage.py migrate
```

**Paso 7 — Levantar el servidor de desarrollo**

```bash
python manage.py runserver
```

La aplicación queda disponible en `http://127.0.0.1:8000/`.

---

## 6. Variables de Entorno

El archivo `.env` no se versiona en el repositorio por razones de seguridad. Copiar `.env.example` como base:

```env
SECRET_KEY='clave-secreta-de-django'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=sgtm_db
DB_USER=sgtm_admin
DB_PASSWORD=contraseña_segura
DB_HOST=localhost
DB_PORT=5432

SECURE_COOKIES=False
```

> **Nota:** Si `SECRET_KEY` contiene caracteres especiales como `#`, debe ir entre comillas simples en el archivo `.env`, ya que el símbolo `#` es interpretado como comentario por los parsers de entorno.

---

## 7. Comandos del Makefile

| Comando         | Descripción                                             |
| --------------- | ------------------------------------------------------- |
| `make install`  | Instala las dependencias listadas en `requirements.txt` |
| `make format`   | Formatea el código automáticamente con Black            |
| `make lint`     | Verifica el cumplimiento de PEP-8 con Flake8            |
| `make test`     | Ejecuta la suite de pruebas con pytest                  |
| `make coverage` | Ejecuta las pruebas y genera el reporte `coverage.xml`  |

---

## 8. Testing y Cobertura

```bash
# Ejecutar todos los tests
make test

# Ejecutar con reporte de cobertura en consola
pytest --cov=. --cov-report=term-missing

# Generar coverage.xml para integración con SonarQube
make coverage
```

**Organización de la suite de pruebas:**

| Archivo                   | Alcance                                             |
| ------------------------- | --------------------------------------------------- |
| `tests/test_models.py`    | Validaciones de modelos y restricciones de datos    |
| `tests/test_services.py`  | Lógica de reserva atómica y control de concurrencia |
| `tests/test_views.py`     | Flujos HTTP y respuestas de las vistas              |
| `tests/test_factories.py` | Correctitud de las factories de usuarios            |

La cobertura actual supera el umbral mínimo del **70%** exigido por el SRS, alcanzando un **~88%** sobre los módulos principales del dominio.

---

## 9. Pipeline de Integración Continua

El pipeline se ejecuta automáticamente en cada `push` o `pull_request` dirigido a las ramas `main` o `develop`.

```
Evento: push / pull_request
    |
    |-- Checkout del código (fetch-depth: 0, requerido por SonarQube)
    |-- Configurar Python 3.12
    |-- make install       (instalación de dependencias)
    |-- make format        (verificación de formato con Black)
    |-- make lint          (verificación PEP-8 con Flake8)
    |-- make coverage      (ejecución de tests + generación de coverage.xml)
    |-- Subir coverage.xml como artefacto del workflow
    |-- Análisis de calidad con SonarQube (servidor UCT)
```

> **Entorno de CI:** En GitHub Actions la base de datos PostgreSQL se reemplaza automáticamente por SQLite en memoria, habilitado mediante la variable de entorno `GITHUB_ACTIONS=true` detectada en `settings.py`. Esto elimina la necesidad de levantar un servicio externo de base de datos en el runner.

---

## 10. Estructura del Proyecto

```
sgtm_proyecto/
|-- .github/
|   `-- workflows/
|       `-- ci.yml              # Definición del pipeline CI/CD
|-- core_sgtm/
|   |-- settings.py             # Configuración centralizada via variables de entorno
|   |-- urls.py                 # Enrutamiento principal
|   `-- wsgi.py
|-- turnos/
|   |-- migrations/             # Migraciones de esquema (gestionadas por Django ORM)
|   |-- tests/
|   |   |-- test_models.py
|   |   |-- test_services.py
|   |   |-- test_views.py
|   |   `-- test_factories.py
|   |-- apps.py                 # Registro del AppConfig y carga de signals
|   |-- factories.py            # Factory de usuarios para el entorno de testing
|   |-- models.py               # Entidades: Usuario, BloqueDisponibilidad, Reserva
|   |-- services.py             # Capa Facade: orquestación de reserva atómica
|   |-- signals.py              # Patrón Observer: registro de auditoría automático
|   `-- views.py                # Controladores de la capa de presentación
|-- .env.example                # Plantilla de variables de entorno
|-- .flake8                     # Configuración del linter (exclusiones y max-line-length)
|-- Makefile                    # Comandos centralizados del proyecto
|-- pytest.ini                  # Configuración del framework de testing
`-- requirements.txt            # Dependencias y versiones del proyecto
```

---

## 11. Reglas de Negocio Implementadas

| Identificador | Descripción                                              | Estado       |
| ------------- | -------------------------------------------------------- | ------------ |
| BR-1          | RUT único e irrepetible por usuario registrado           | Implementado |
| BR-6 / BR-7   | Sin superposición de bloques en la agenda del médico     | Implementado |
| BR-8          | Bloqueo de reservas sobre fechas y horas pasadas         | Implementado |
| BR-13         | Reserva atómica sin doble booking concurrente            | Implementado |
| BR-18 / BR-19 | Ciclo de vida formal de estados del turno                | Implementado |
| NFR-8         | Integridad transaccional mediante `transaction.atomic()` | Implementado |
| NFR-12        | Auditoría automática de operaciones via Django Signals   | Implementado |

---

## 12. Equipo de Desarrollo

| Integrante      | Rol                             | Responsabilidades                                                                                          |
| --------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Edgar Melgarejo | DevOps / Arquitectura / Calidad | Pipeline CI/CD, integración SonarQube, diseño arquitectónico, suite de pruebas unitarias (cobertura > 70%) |
| Rodrigo Reyes   | Seguridad / Backend             | Autenticación JWT, Refresh Tokens, controladores REST, pruebas de integración                              |
| Benjamín Parra  | Frontend / Testing E2E          | Interfaz de usuario, panel de recepcionista, pruebas End-to-End (Cypress/Selenium)                         |

---

_Universidad Católica de Temuco — Ingeniería en Informática — 2026_
