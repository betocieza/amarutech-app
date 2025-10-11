-- Tabla para preguntas frecuentes (FAQs)
CREATE TABLE faqs (
    faq_id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    enabled BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento
CREATE INDEX idx_faqs_category ON faqs(category);
CREATE INDEX idx_faqs_enabled ON faqs(enabled);
CREATE INDEX idx_faqs_sort_order ON faqs(sort_order);
CREATE INDEX idx_faqs_category_enabled ON faqs(category, enabled);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_faqs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER trigger_faqs_updated_at
    BEFORE UPDATE ON faqs
    FOR EACH ROW
    EXECUTE PROCEDURE update_faqs_updated_at();

-- Insertar datos de ejemplo (FAQs de consultoría)
INSERT INTO faqs (question, answer, category, sort_order, enabled) VALUES
('¿Qué incluye el servicio de consultoría?', 'Nuestro servicio de consultoría incluye análisis de requerimientos, arquitectura de software, selección de tecnologías, planificación de proyecto, estimación de tiempos y costos, y recomendaciones de mejores prácticas.', 'consulting', 1, TRUE),
('¿Cómo evalúan la viabilidad de un proyecto?', 'Realizamos un análisis técnico y comercial completo que incluye evaluación de recursos, factibilidad técnica, análisis de riesgos, estimación de ROI y definición de hitos del proyecto.', 'consulting', 2, TRUE),
('¿Ofrecen consultoría para migración de sistemas?', 'Sí, ayudamos en la migración de sistemas legacy a tecnologías modernas, incluyendo análisis del sistema actual, estrategia de migración, minimización de riesgos y plan de transición.', 'consulting', 3, TRUE),
('¿Pueden ayudar con la optimización de procesos?', 'Definitivamente. Analizamos sus procesos actuales, identificamos áreas de mejora, proponemos automatizaciones y diseñamos soluciones que optimicen la eficiencia operativa.', 'consulting', 4, TRUE),
('¿Qué entregables proporciona la consultoría?', 'Entregamos documentación técnica completa, arquitectura del sistema, especificaciones funcionales, cronograma del proyecto, análisis de riesgos y recomendaciones estratégicas.', 'consulting', 5, TRUE);

-- Insertar datos de ejemplo (FAQs generales)
INSERT INTO faqs (question, answer, category, sort_order, enabled) VALUES
('¿Qué servicios de desarrollo de software ofrecen?', 'Ofrecemos desarrollo de aplicaciones web, móviles, sistemas de gestión, e-commerce, APIs, y soluciones personalizadas utilizando las tecnologías más modernas como Angular, React, Node.js, y más.', 'general', 1, TRUE),
('¿Cuánto tiempo toma desarrollar un proyecto?', 'El tiempo de desarrollo varía según la complejidad del proyecto. Un sitio web básico puede tomar 2-4 semanas, mientras que aplicaciones más complejas pueden requerir 3-6 meses. Siempre proporcionamos un cronograma detallado antes de comenzar.', 'general', 2, TRUE),
('¿Ofrecen soporte post-lanzamiento?', 'Sí, ofrecemos soporte técnico completo después del lanzamiento, incluyendo mantenimiento, actualizaciones, corrección de errores y nuevas funcionalidades. Tenemos diferentes planes de soporte adaptados a sus necesidades.', 'general', 3, TRUE),
('¿Trabajan con empresas de todos los tamaños?', 'Absolutamente. Trabajamos con startups, PyMEs y grandes empresas. Adaptamos nuestros servicios y metodologías según el tamaño y necesidades específicas de cada cliente.', 'general', 4, TRUE),
('¿Qué tecnologías utilizan?', 'Utilizamos tecnologías modernas y probadas como Angular, React, Vue.js, Node.js, Python, Java, .NET, bases de datos SQL y NoSQL, servicios en la nube (AWS, Azure), y metodologías ágiles.', 'general', 5, TRUE),
('¿Cómo puedo obtener una cotización?', 'Puede contactarnos a través de nuestro formulario web, email o teléfono. Programaremos una reunión para entender sus necesidades y le proporcionaremos una cotización detallada sin compromiso.', 'general', 6, TRUE);