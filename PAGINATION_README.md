# Documentación de Paginación para Posts

## Resumen
Se ha agregado funcionalidad de paginación al método `get_posts()` del sistema de posts para mejorar el rendimiento y la experiencia del usuario al manejar grandes cantidades de posts.

## Cambios Realizados

### 1. PostService - Método `get_posts()`
**Antes:**
```python
def get_posts(cls):
    # Retornaba todos los posts como lista
    return posts
```

**Después:**
```python
def get_posts(cls, page=1, per_page=10):
    # Retorna posts paginados con información de paginación
    return {
        'posts': posts,
        'pagination': {
            'page': 1,
            'per_page': 10,
            'total': 25,
            'pages': 3,
            'has_prev': False,
            'prev_num': None,
            'has_next': True,
            'next_num': 2
        }
    }
```

### 2. Nuevo Método de Compatibilidad
```python
def get_all_posts(cls):
    # Método para mantener compatibilidad con código existente
    # Retorna solo la lista de posts sin paginación
```

### 3. Controlador Actualizado
**Ruta principal:** `GET /posts/all`
- Acepta parámetros `page` y `per_page` como query parameters
- Retorna respuesta estructurada con datos y paginación

**Nueva ruta:** `GET /posts/all/no-pagination`
- Retorna todos los posts sin paginación
- Para mantener compatibilidad con clientes existentes

## Uso de la API

### Obtener Posts con Paginación
```http
GET /posts/all?page=1&per_page=10
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
    "success": true,
    "data": [
        {
            "post_id": 1,
            "title": "Título del Post",
            "slug": "titulo-del-post",
            "description": "Descripción...",
            "category_id": 1,
            "user_id": 1,
            "published": true,
            "created_at": "2025-10-10T12:00:00",
            "updated_at": "2025-10-10T12:00:00",
            "image_url": null,
            "tags": ["tag1", "tag2"]
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

### Obtener Todos los Posts (Sin Paginación)
```http
GET /posts/all/no-pagination
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
    "success": true,
    "data": [...], // Todos los posts
    "total": 25
}
```

## Parámetros de Paginación

| Parámetro | Tipo | Valor por Defecto | Descripción |
|-----------|------|-------------------|-------------|
| `page` | integer | 1 | Número de página (mínimo: 1) |
| `per_page` | integer | 10 | Posts por página (máximo: 100) |

## Información de Paginación Retornada

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `page` | integer | Página actual |
| `per_page` | integer | Posts por página |
| `total` | integer | Total de posts en la base de datos |
| `pages` | integer | Total de páginas disponibles |
| `has_prev` | boolean | Si existe página anterior |
| `prev_num` | integer/null | Número de página anterior |
| `has_next` | boolean | Si existe página siguiente |
| `next_num` | integer/null | Número de página siguiente |

## Validaciones Implementadas

1. **Página mínima:** Si se envía `page < 1`, se convierte automáticamente a `1`
2. **Posts por página:** El valor máximo es `100` para evitar sobrecarga del servidor
3. **Manejo de errores:** Si hay problemas, retorna estructura vacía con paginación por defecto

## Beneficios

1. **Rendimiento:** Reduce la carga del servidor al no cargar todos los posts de una vez
2. **Experiencia de usuario:** Permite navegación más rápida en listas grandes
3. **Escalabilidad:** El sistema puede manejar miles de posts sin problemas
4. **Compatibilidad:** El código existente sigue funcionando con el nuevo endpoint

## Migración para Clientes Existentes

### Opción 1: Usar el nuevo endpoint con paginación
```javascript
// Antes
const response = await fetch('/posts/all');
const posts = await response.json();

// Después
const response = await fetch('/posts/all?page=1&per_page=10');
const result = await response.json();
const posts = result.data;
const pagination = result.pagination;
```

### Opción 2: Usar el endpoint de compatibilidad
```javascript
// Cambio mínimo
const response = await fetch('/posts/all/no-pagination');
const result = await response.json();
const posts = result.data;
```

## Ejemplos de Uso Frontend

### React Component con Paginación
```jsx
function PostsList() {
    const [posts, setPosts] = useState([]);
    const [pagination, setPagination] = useState({});
    const [currentPage, setCurrentPage] = useState(1);
    
    const loadPosts = async (page = 1) => {
        const response = await fetch(`/posts/all?page=${page}&per_page=10`);
        const data = await response.json();
        
        if (data.success) {
            setPosts(data.data);
            setPagination(data.pagination);
            setCurrentPage(page);
        }
    };
    
    return (
        <div>
            {posts.map(post => (
                <PostItem key={post.post_id} post={post} />
            ))}
            
            <Pagination 
                current={currentPage}
                total={pagination.pages}
                onChange={loadPosts}
                hasNext={pagination.has_next}
                hasPrev={pagination.has_prev}
            />
        </div>
    );
}
```

## Consideraciones de Rendimiento

1. **Índices de base de datos:** Asegúrate de que la tabla `posts` tenga índices en `created_at` para ordenamiento eficiente
2. **Cache:** Considera implementar cache para páginas frecuentemente accedidas
3. **Lazy loading:** Implementa carga bajo demanda en el frontend

## Testing

Ejecutar el script de prueba:
```bash
python test_pagination.py
```

Este script verifica:
- Funcionalidad básica de paginación
- Validación de parámetros
- Compatibilidad entre métodos
- Manejo de casos edge