-- Script para crear sliders de prueba
-- Ejecutar después de las migraciones para poblar la tabla con datos de ejemplo

INSERT INTO sliders (title, subtitle, link, image_url, published, sort_order, created_at, updated_at) VALUES
(
    'Desarrollo Web Profesional',
    'Creamos sitios web modernos y responsivos con las últimas tecnologías',
    'https://amarutech.com/servicios/desarrollo-web',
    'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=600&fit=crop',
    TRUE,
    1,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    'Aplicaciones Móviles',
    'Desarrollamos apps nativas e híbridas para iOS y Android',
    'https://amarutech.com/servicios/apps-moviles',
    'https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=1200&h=600&fit=crop',
    TRUE,
    2,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    'Consultoría Tecnológica',
    'Asesoramiento especializado para la transformación digital de tu empresa',
    'https://amarutech.com/servicios/consultoria',
    'https://images.unsplash.com/photo-1552664730-d307ca884978?w=1200&h=600&fit=crop',
    TRUE,
    3,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    'Soporte y Mantenimiento',
    'Servicios de soporte 24/7 y mantenimiento continuo para tus proyectos',
    'https://amarutech.com/servicios/soporte',
    'https://images.unsplash.com/photo-1551434678-e076c223a692?w=1200&h=600&fit=crop',
    TRUE,
    4,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Verificar los sliders creados
-- SELECT slider_id, title, sort_order, published, created_at 
-- FROM sliders 
-- ORDER BY sort_order ASC;