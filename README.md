# AmaruTech CMS API

API REST para sistema de gestión de contenidos desarrollada con Flask y SQLAlchemy ORM.

## 🚀 Características

- ✅ **API REST completa** para gestión de posts, categorías, usuarios y sliders
- ✅ **Autenticación JWT** con roles de usuario
- ✅ **SQLAlchemy ORM** para gestión de base de datos
- ✅ **Upload de imágenes a Backblaze B2** con validación
- ✅ **Sistema de tags** con soporte JSON
- ✅ **Logging estructurado** para debugging
- ✅ **Arquitectura MVC** bien organizada

## 📁 Estructura del Proyecto

```
amarutech-app/
├── src/
│   ├── controllers/         # Controladores de API endpoints
│   ├── models/             # Modelos ORM y DTOs
│   ├── services/           # Lógica de negocio
│   ├── database/           # Configuración de BD
│   └── utils/              # Utilidades (Security, Logger)
├── config.py               # Configuración
├── index.py               # Punto de entrada
├── requirements.txt       # Dependencias
└── vercel.json           # Deploy config
```

## 🛠️ Instalación

### 1. Entorno virtual
```bash
python -m venv venv
venv\Scripts\Activate.ps1  # Windows
```

### 2. Dependencias
```bash
pip install -r requirements.txt
```

### 3. Variables de entorno (.env)
```env
SECRET_KEY=tu_secret_key
JWT_KEY=tu_jwt_key
POSTGRES_USER=usuario_bd
POSTGRES_PASSWORD=password_bd
POSTGRES_HOST=localhost
POSTGRES_DATABASE=amarutech_cms
B2_KEY_ID=tu_b2_key_id
B2_APP_KEY=tu_b2_app_key
B2_BUCKET_NAME=tu_bucket_name
```

### 4. Ejecutar
```bash
python index.py
```

## 📚 API Endpoints

### 🔐 Autenticación
```
POST /api/auth/login
```

### 📝 Posts (con tags y upload de imágenes)
```
GET    /api/posts/         # Lista posts
POST   /api/posts/create   # Crear con imagen opcional
PUT    /api/posts/update/<id>  # Actualizar
POST   /api/posts/upload   # Upload imagen individual
```

### 📂 Categorías, 👥 Usuarios, 🎨 Sliders
```
GET/POST/PUT endpoints disponibles
```

## 📝 Formato JSON para Posts

```json
{
  "title": "Mi Post",
  "slug": "mi-post", 
  "description": "Descripción",
  "category_id": 1,
  "published": true,
  "tags": ["python", "flask", "api"]
}
```

## 🚀 Tecnologías

- Flask 3.1.0 + SQLAlchemy 2.0.38
- PostgreSQL + PyJWT 2.10.1  
- Backblaze B2 SDK + Flask-Cors
- Docker + Vercel ready
