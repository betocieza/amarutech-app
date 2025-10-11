# Migraciones de Base de Datos

Este proyecto utiliza Flask-Migrate (Alembic) para manejar las migraciones de base de datos.

## Comandos de Migración

### Configuración Inicial
```bash
# Instalar dependencias
pip install Flask-Migrate python-dotenv

# Inicializar el repositorio de migraciones (solo una vez)
flask db init
```

### Crear Migraciones
```bash
# Generar una migración automática basada en cambios en los modelos
flask db migrate -m "Descripción del cambio"

# Crear una migración vacía (para cambios manuales)
flask db revision -m "Descripción del cambio"
```

### Aplicar Migraciones
```bash
# Aplicar todas las migraciones pendientes
flask db upgrade

# Aplicar hasta una revisión específica
flask db upgrade <revision_id>

# Revertir a una revisión anterior
flask db downgrade <revision_id>
```

### Información de Migraciones
```bash
# Ver el estado actual de las migraciones
flask db current

# Ver el historial de migraciones
flask db history

# Ver las migraciones pendientes
flask db show
```

## Estructura de Archivos

```
migrations/
├── alembic.ini          # Configuración de Alembic
├── env.py              # Configuración del entorno de migración
├── README              # Documentación de Alembic
├── script.py.mako      # Template para nuevas migraciones
└── versions/           # Archivos de migración
    └── d3f7ea5b4b8b_add_faq_table_with_enabled_field.py
```

## Migración Actual

### 2dbea6e6d8f4 - Add sort_order field to sliders table

Esta migración incluye:

- **Nuevo campo `sort_order`** en la tabla `sliders`:
  - `sort_order` (Integer, Default: 0): Campo para ordenar sliders

### d3f7ea5b4b8b - Add FAQ table with enabled field

Esta migración incluye:

- **Tabla `faqs`** con los siguientes campos:
  - `faq_id` (Integer, Primary Key): ID único de la FAQ
  - `question` (Text, NOT NULL): Pregunta de la FAQ
  - `answer` (Text, NOT NULL): Respuesta de la FAQ
  - `category` (String(100)): Categoría de la FAQ ('consulting', 'general', etc.)
  - `enabled` (Boolean, Default: True): Estado de habilitación de la FAQ
  - `sort_order` (Integer, Default: 0): Orden de visualización
  - `created_at` (DateTime): Fecha de creación
  - `updated_at` (DateTime): Fecha de última actualización

## Datos de Ejemplo

Para poblar la tabla con datos de ejemplo, usar el endpoint:
```bash
POST /api/faqs/seed
```

Esto creará:
- 5 FAQs de consultoría (category: 'consulting')
- 6 FAQs generales (category: 'general')

## Notas Importantes

1. **Antes de ejecutar migraciones en producción**, siempre hacer backup de la base de datos
2. **Revisar los archivos de migración** antes de aplicarlos
3. **Probar las migraciones** en un entorno de desarrollo primero
4. **Las migraciones son incrementales** - deben aplicarse en orden

## Variables de Entorno Requeridas

Asegúrate de tener configuradas las siguientes variables en tu archivo `.env`:

```
SECRET_KEY=tu_clave_secreta
POSTGRES_USER=usuario_db
POSTGRES_PASSWORD=password_db
POSTGRES_HOST=localhost
POSTGRES_DATABASE=nombre_db
```

## Comandos de Ejemplo

```bash
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Crear nueva migración después de cambiar modelos
flask db migrate -m "Add new field to User table"

# Aplicar migraciones
flask db upgrade

# Ver estado actual
flask db current
```