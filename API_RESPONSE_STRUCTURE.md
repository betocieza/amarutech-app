# Estructura Completa de Respuesta - Método get_posts()

## Endpoint
```
GET /posts/all
Authorization: Bearer <token>
```

## Parámetros Query (Opcionales)
```
?page=1&per_page=10
```

## Estructura de Respuesta

### 1. Respuesta Exitosa CON Posts

**HTTP Status:** `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "post_id": 1,
      "title": "Título del Post",
      "slug": "titulo-del-post",
      "description": "Descripción completa del contenido del post",
      "category_id": 1,
      "user_id": 1,
      "published": true,
      "created_at": "2025-10-10T12:30:45",
      "updated_at": "2025-10-10T14:15:30",
      "image_url": "https://example.com/images/post.jpg",
      "tags": ["tag1", "tag2", "tag3"]
    },
    {
      "post_id": 2,
      "title": "Segundo Post",
      "slug": "segundo-post",
      "description": "Otra descripción de ejemplo",
      "category_id": 2,
      "user_id": 1,
      "published": false,
      "created_at": "2025-10-09T08:15:22",
      "updated_at": "2025-10-09T10:45:18",
      "image_url": null,
      "tags": []
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "pages": 3,
    "has_prev": false,
    "prev_num": null,
    "has_next": true,
    "next_num": 2
  }
}
```

### 2. Respuesta Exitosa SIN Posts

**HTTP Status:** `200 OK`

```json
{
  "success": true,
  "message": "No posts found",
  "data": [],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 0,
    "pages": 0,
    "has_prev": false,
    "prev_num": null,
    "has_next": false,
    "next_num": null
  }
}
```

### 3. Respuesta de Error del Servidor

**HTTP Status:** `500 Internal Server Error`

```json
{
  "message": "Internal server error",
  "success": false
}
```

### 4. Respuesta Sin Autorización

**HTTP Status:** `401 Unauthorized`

```json
{
  "message": "Unauthorized"
}
```

## Descripción de Campos

### Objeto Principal
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | `boolean` | Indica si la operación fue exitosa |
| `data` | `array` | Array de objetos Post |
| `pagination` | `object` | Información de paginación |
| `message` | `string` | Mensaje descriptivo (solo cuando no hay posts o error) |

### Objeto Post (dentro de `data`)
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `post_id` | `integer` | ✅ | ID único del post |
| `title` | `string` | ✅ | Título del post |
| `slug` | `string` | ✅ | Slug URL-friendly |
| `description` | `string` | ✅ | Descripción/contenido del post |
| `category_id` | `integer` | ✅ | ID de la categoría |
| `user_id` | `integer` | ✅ | ID del usuario autor |
| `published` | `boolean` | ✅ | Estado de publicación |
| `created_at` | `string` | ✅ | Fecha de creación (ISO 8601) |
| `updated_at` | `string` | ✅ | Fecha de última actualización (ISO 8601) |
| `image_url` | `string\|null` | ❌ | URL de la imagen del post |
| `tags` | `array` | ❌ | Array de strings con etiquetas |

### Objeto Pagination
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `page` | `integer` | Página actual |
| `per_page` | `integer` | Elementos por página |
| `total` | `integer` | Total de posts en la base de datos |
| `pages` | `integer` | Total de páginas disponibles |
| `has_prev` | `boolean` | Indica si existe página anterior |
| `prev_num` | `integer\|null` | Número de página anterior |
| `has_next` | `boolean` | Indica si existe página siguiente |
| `next_num` | `integer\|null` | Número de página siguiente |

## Tipos de Datos Detallados

### Campos de Post
```typescript
interface Post {
  post_id: number;           // Entero positivo
  title: string;             // Máximo 255 caracteres
  slug: string;              // Máximo 255 caracteres, URL-friendly
  description: string;       // Texto largo
  category_id: number;       // Entero positivo, FK a categories
  user_id: number;           // Entero positivo, FK a users
  published: boolean;        // true/false
  created_at: string;        // ISO 8601: "YYYY-MM-DDTHH:mm:ss"
  updated_at: string;        // ISO 8601: "YYYY-MM-DDTHH:mm:ss"
  image_url: string | null;  // URL válida o null
  tags: string[];            // Array de strings
}
```

### Valores Posibles

#### `published`
- `true`: Post publicado y visible
- `false`: Post en borrador

#### `image_url`
- `string`: URL completa de la imagen (ej: "https://domain.com/image.jpg")
- `null`: Sin imagen asociada

#### `tags`
- `[]`: Array vacío (sin etiquetas)
- `["tag1", "tag2"]`: Array con etiquetas como strings

#### Fechas (`created_at`, `updated_at`)
- Formato: ISO 8601 sin zona horaria
- Ejemplo: `"2025-10-10T14:15:30"`
- Siempre en UTC

## Ejemplos de Uso

### JavaScript/Frontend
```javascript
// Obtener primera página
const response = await fetch('/posts/all?page=1&per_page=10', {
  headers: {
    'Authorization': 'Bearer ' + token
  }
});

const result = await response.json();

if (result.success) {
  const posts = result.data;
  const pagination = result.pagination;
  
  // Procesar posts
  posts.forEach(post => {
    console.log(`Post: ${post.title}`);
    console.log(`Publicado: ${post.published ? 'Sí' : 'No'}`);
    console.log(`Tags: ${post.tags.join(', ')}`);
  });
  
  // Manejar paginación
  if (pagination.has_next) {
    console.log(`Siguiente página: ${pagination.next_num}`);
  }
}
```

### cURL
```bash
# Obtener posts con paginación
curl -X GET "http://localhost:5000/posts/all?page=1&per_page=5" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## Validaciones y Límites

1. **Paginación:**
   - `page`: Mínimo 1, se convierte automáticamente si es menor
   - `per_page`: Máximo 100, se limita automáticamente

2. **Autorización:**
   - Requerido token JWT válido en header Authorization
   - Sin token: HTTP 401

3. **Campos de Post:**
   - `title`, `slug`, `description`: No pueden ser null ni vacíos
   - `category_id`, `user_id`: Deben ser enteros positivos válidos
   - `tags`: Siempre es array, nunca null

## Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| `200` | Éxito - Posts obtenidos (con o sin datos) |
| `401` | No autorizado - Token inválido o faltante |
| `500` | Error interno del servidor |

## Compatibilidad

Para código que necesite solo la lista de posts sin paginación, usar:
```
GET /posts/all/no-pagination
```

Respuesta simplificada:
```json
{
  "success": true,
  "data": [...],
  "total": 25
}
```