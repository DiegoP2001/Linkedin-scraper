# 🧠 Automatización Inteligente para Gestión de LinkedIn, Contactos y Tareas Programadas

Este proyecto es una plataforma backend desarrollada en **Python + Flask + Selenium** que permite a los usuarios autenticados automatizar procesos relacionados con **LinkedIn**, **correo electrónico**, **scraping de datos**, **mensajería**, **listas personalizadas** y **tareas programadas**, utilizando **Celery** como motor de ejecución asíncrona.

### 🚀 Objetivos Principales

- Automatizar tareas complejas como conexión con miembros de LinkedIn, envío masivo de mensajes o emails, scraping de información, entre otros.
- Permitir a los usuarios configurar y lanzar estas tareas bajo demanda o de forma programada (diaria, semanal, etc.).
- Gestionar contactos valiosos, crear listas personalizadas y mantener un histórico de resultados.
- Ofrecer control total sobre las tareas activas y ejecutadas, permitiendo consultar su estado en tiempo real.
- Brindar una API robusta y segura que pueda ser consumida por una interfaz web o móvil.

---

### 🧩 Funcionalidades Clave

#### 🔐 Autenticación & Gestión de Usuario
- Login con JWT (Access & Refresh Token).
- Recuperación y cambio de contraseña.
- Actualización de datos personales y redes sociales.
- Panel administrativo para crear y editar usuarios.

#### 📄 Scraping & Análisis de Datos
- Scraping de perfiles y resultados de LinkedIn.
- Scraping profundo (detalles avanzados del perfil).
- Consulta de historial de scraping.
- Identificación de contactos valiosos.

#### 🤝 Mensajería & Conexiones
- Conexión automatizada con miembros valiosos.
- Envío de mensajes personalizados.
- Historial de mensajes vinculados a contactos.

#### 🧠 Integración con GPT
- Procesamiento de listas y contactos mediante modelos de lenguaje (GPT).
- Contextualización con parámetros y filtros personalizados.

#### 📂 Listas & Filtros
- Creación y gestión de listas personalizadas de contactos.
- Añadir/quitar miembros de listas.
- Grupos de filtros reutilizables para búsquedas.

#### 📆 Tareas Programadas con Celery
- Programación de tareas de forma puntual o recurrente (diaria/semanal).
- Listado de tareas activas por usuario.
- Consulta de tareas en ejecución y tareas Celery disponibles.
- Eliminación segura de tareas programadas.
- Estado en tiempo real de cada tarea (`PENDING`, `STARTED`, `SUCCESS`, `FAILURE`, etc.).

---

### 🛠️ Tecnologías Utilizadas

- **Flask** — Framework principal para la API REST.
- **SQLAlchemy** — ORM para modelos y consultas a la base de datos.
- **Celery + Redis + RabbitMQ** — Para ejecución de tareas en segundo plano.
- **JWT (Flask-JWT-Extended)** — Para autenticación segura.
- **WebPush** — Envío de notificaciones a usuarios.
- **OpenAI GPT** — Procesamiento de datos basado en lenguaje natural.
- **SQLite / PostgreSQL** — Bases de datos compatibles.
- **Selenium** — Para tareas de scraping dinámico.

---

### 📡 Endpoints Destacados

- `/api/login`, `/api/logout`, `/api/check_auth`
- `/api/connect-valuable-members`, `/api/send-message`
- `/api/scrap-data-from-linkedin`, `/api/deep-scrapp`
- `/api/send-massive-emails`, `/api/send-data-to-gpt`
- `/api/custom-lists/...` (gestión completa de listas)
- `/api/schedule-task`, `/api/task-status`, `/api/get-active-tasks`
- `/api/get-available-tasks`, `/api/get-task-params`
- `/api/user/account/...` (cambio de contraseña, redes sociales, info personal)

---

### 🧪 Ejemplo de Flujo de Uso

1. El usuario inicia sesión y se autentica con JWT.
2. Desde el frontend selecciona una tarea (ej: conectar con miembros de LinkedIn).
3. Define parámetros, fecha, hora y si la tarea debe repetirse.
4. La tarea es registrada y programada mediante Celery.
5. Puede consultar el estado en tiempo real desde `/api/task-status`.
6. Recibe notificaciones push y puede revisar los resultados y mensajes enviados.

---

### 🔐 Seguridad

- Todas las rutas protegidas por `@token_required`.
- CORS configurado por entorno (`localhost` en dev, dominio real en producción).
- Validación de propiedad en todas las entidades (por `user_id`).
- Cookies seguras para JWT.

---

### 🧠 Autor / Colaborador

> Este proyecto fue documentado y optimizado con ❤️ por **Diego Piedra**.
