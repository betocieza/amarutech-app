import traceback
# SQLAlchemy
from src.models.FaqEntity import FaqEntity
from src.database import db
# Logger
from src.utils.Logger import Logger
# Models
from src.models.FaqEntity import Faq

class FaqService():

    @classmethod
    def get_faqs(cls, category=None, enabled_only=True):
        """Obtener todas las FAQs, opcionalmente filtradas por categoría"""
        try:
            query = FaqEntity.query
            
            if enabled_only:
                query = query.filter_by(enabled=True)
                
            if category:
                query = query.filter_by(category=category)
                
            # Ordenar por sort_order y luego por fecha de creación
            faq_entities = query.order_by(FaqEntity.sort_order.asc(), FaqEntity.created_at.asc()).all()
            
            faqs = []
            for faq_entity in faq_entities:
                faq = Faq(
                    faq_id=faq_entity.faq_id,
                    question=faq_entity.question,
                    answer=faq_entity.answer,
                    category=faq_entity.category,
                    enabled=faq_entity.enabled,
                    sort_order=faq_entity.sort_order,
                    created_at=faq_entity.created_at,
                    updated_at=faq_entity.updated_at
                )
                faqs.append(faq.to_json())
            return faqs
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return []

    @classmethod
    def get_faq_by_id(cls, faq_id):
        """Obtener una FAQ por ID"""
        try:
            faq_entity = FaqEntity.query.get(faq_id)
            if faq_entity:
                return faq_entity.to_dict()
            return None
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return None

    @classmethod
    def get_faqs_by_category(cls, category, enabled_only=True):
        """Obtener FAQs por categoría específica"""
        return cls.get_faqs(category=category, enabled_only=enabled_only)

    @classmethod
    def save_faq(cls, faq):
        """Crear una nueva FAQ"""
        try:
            new_faq = FaqEntity(
                question=faq.question,
                answer=faq.answer,
                category=faq.category,
                enabled=faq.enabled if hasattr(faq, 'enabled') else True,
                sort_order=faq.sort_order if hasattr(faq, 'sort_order') else 0
            )
            db.session.add(new_faq)
            db.session.commit()
            return "FAQ creada exitosamente"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error al crear FAQ"

    @classmethod
    def update_faq(cls, faq_id, faq):
        """Actualizar una FAQ existente"""
        try:
            faq_entity = FaqEntity.query.get(faq_id)
            if faq_entity:
                faq_entity.question = faq.question
                faq_entity.answer = faq.answer
                faq_entity.category = faq.category
                faq_entity.enabled = faq.enabled if hasattr(faq, 'enabled') else faq_entity.enabled
                faq_entity.sort_order = faq.sort_order if hasattr(faq, 'sort_order') else faq_entity.sort_order
                
                db.session.commit()
                return "FAQ actualizada exitosamente"
            return "FAQ no encontrada"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error al actualizar FAQ"

    @classmethod
    def delete_faq(cls, faq_id):
        """Eliminar una FAQ (eliminación física)"""
        try:
            faq_entity = FaqEntity.query.get(faq_id)
            if faq_entity:
                db.session.delete(faq_entity)
                db.session.commit()
                return "FAQ eliminada exitosamente"
            return "FAQ no encontrada"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error al eliminar FAQ"

    @classmethod
    def toggle_faq_enabled(cls, faq_id):
        """Cambiar el estado enabled de una FAQ"""
        try:
            faq_entity = FaqEntity.query.get(faq_id)
            if faq_entity:
                faq_entity.enabled = not faq_entity.enabled
                db.session.commit()
                status = "habilitada" if faq_entity.enabled else "deshabilitada"
                return f"FAQ {status} exitosamente"
            return "FAQ no encontrada"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error al cambiar estado de FAQ"

    @classmethod
    def update_faq_sort_order(cls, faq_id, sort_order):
        """Actualizar el orden de una FAQ"""
        try:
            faq_entity = FaqEntity.query.get(faq_id)
            if faq_entity:
                faq_entity.sort_order = sort_order
                db.session.commit()
                return "Orden de FAQ actualizado exitosamente"
            return "FAQ no encontrada"
        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error al actualizar orden de FAQ"

    @classmethod
    def seed_default_faqs(cls):
        """Poblar la base de datos con las FAQs por defecto"""
        try:
            # Verificar si ya existen FAQs
            existing_faqs = FaqEntity.query.count()
            if existing_faqs > 0:
                return "Las FAQs ya existen en la base de datos"

            # FAQs de consultoría
            consulting_faqs = [
                {
                    'question': '¿Qué incluye el servicio de consultoría?',
                    'answer': 'Nuestro servicio de consultoría incluye análisis de requerimientos, arquitectura de software, selección de tecnologías, planificación de proyecto, estimación de tiempos y costos, y recomendaciones de mejores prácticas.',
                    'category': 'consulting',
                    'sort_order': 1
                },
                {
                    'question': '¿Cómo evalúan la viabilidad de un proyecto?',
                    'answer': 'Realizamos un análisis técnico y comercial completo que incluye evaluación de recursos, factibilidad técnica, análisis de riesgos, estimación de ROI y definición de hitos del proyecto.',
                    'category': 'consulting',
                    'sort_order': 2
                },
                {
                    'question': '¿Ofrecen consultoría para migración de sistemas?',
                    'answer': 'Sí, ayudamos en la migración de sistemas legacy a tecnologías modernas, incluyendo análisis del sistema actual, estrategia de migración, minimización de riesgos y plan de transición.',
                    'category': 'consulting',
                    'sort_order': 3
                },
                {
                    'question': '¿Pueden ayudar con la optimización de procesos?',
                    'answer': 'Definitivamente. Analizamos sus procesos actuales, identificamos áreas de mejora, proponemos automatizaciones y diseñamos soluciones que optimicen la eficiencia operativa.',
                    'category': 'consulting',
                    'sort_order': 4
                },
                {
                    'question': '¿Qué entregables proporciona la consultoría?',
                    'answer': 'Entregamos documentación técnica completa, arquitectura del sistema, especificaciones funcionales, cronograma del proyecto, análisis de riesgos y recomendaciones estratégicas.',
                    'category': 'consulting',
                    'sort_order': 5
                }
            ]

            # FAQs generales
            general_faqs = [
                {
                    'question': '¿Qué servicios de desarrollo de software ofrecen?',
                    'answer': 'Ofrecemos desarrollo de aplicaciones web, móviles, sistemas de gestión, e-commerce, APIs, y soluciones personalizadas utilizando las tecnologías más modernas como Angular, React, Node.js, y más.',
                    'category': 'general',
                    'sort_order': 1
                },
                {
                    'question': '¿Cuánto tiempo toma desarrollar un proyecto?',
                    'answer': 'El tiempo de desarrollo varía según la complejidad del proyecto. Un sitio web básico puede tomar 2-4 semanas, mientras que aplicaciones más complejas pueden requerir 3-6 meses. Siempre proporcionamos un cronograma detallado antes de comenzar.',
                    'category': 'general',
                    'sort_order': 2
                },
                {
                    'question': '¿Ofrecen soporte post-lanzamiento?',
                    'answer': 'Sí, ofrecemos soporte técnico completo después del lanzamiento, incluyendo mantenimiento, actualizaciones, corrección de errores y nuevas funcionalidades. Tenemos diferentes planes de soporte adaptados a sus necesidades.',
                    'category': 'general',
                    'sort_order': 3
                },
                {
                    'question': '¿Trabajan con empresas de todos los tamaños?',
                    'answer': 'Absolutamente. Trabajamos con startups, PyMEs y grandes empresas. Adaptamos nuestros servicios y metodologías según el tamaño y necesidades específicas de cada cliente.',
                    'category': 'general',
                    'sort_order': 4
                },
                {
                    'question': '¿Qué tecnologías utilizan?',
                    'answer': 'Utilizamos tecnologías modernas y probadas como Angular, React, Vue.js, Node.js, Python, Java, .NET, bases de datos SQL y NoSQL, servicios en la nube (AWS, Azure), y metodologías ágiles.',
                    'category': 'general',
                    'sort_order': 5
                },
                {
                    'question': '¿Cómo puedo obtener una cotización?',
                    'answer': 'Puede contactarnos a través de nuestro formulario web, email o teléfono. Programaremos una reunión para entender sus necesidades y le proporcionaremos una cotización detallada sin compromiso.',
                    'category': 'general',
                    'sort_order': 6
                }
            ]

            # Insertar FAQs de consultoría
            for faq_data in consulting_faqs:
                faq = FaqEntity(
                    question=faq_data['question'],
                    answer=faq_data['answer'],
                    category=faq_data['category'],
                    sort_order=faq_data['sort_order'],
                    enabled=True
                )
                db.session.add(faq)

            # Insertar FAQs generales
            for faq_data in general_faqs:
                faq = FaqEntity(
                    question=faq_data['question'],
                    answer=faq_data['answer'],
                    category=faq_data['category'],
                    sort_order=faq_data['sort_order'],
                    enabled=True
                )
                db.session.add(faq)

            db.session.commit()
            return "FAQs por defecto creadas exitosamente"

        except Exception as ex:
            db.session.rollback()
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())
            return "Error al crear FAQs por defecto"