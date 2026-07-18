import os
import traceback
import uuid
from io import BytesIO
from PIL import Image
from werkzeug.utils import secure_filename
from src.database.b2_connection import bucket, b2_api
from src.utils.Logger import Logger

WEBP_QUALITY = 80


def convert_to_webp(file_data, file_ext):
    """
    Convierte los bytes de una imagen a WebP.

    Returns:
        tuple: (webp_bytes, converted) — converted es False si no se pudo
        convertir (ej. GIF animado) y se debe usar el archivo original.
    """
    try:
        image = Image.open(BytesIO(file_data))

        # No recodificar GIFs animados: WebP animado requiere manejo especial
        if file_ext == '.gif' and getattr(image, 'is_animated', False):
            return file_data, False

        # RGBA/LA/P conservan transparencia; el resto se pasa a RGB
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            image = image.convert('RGBA')
        else:
            image = image.convert('RGB')

        output = BytesIO()
        image.save(output, format='WEBP', quality=WEBP_QUALITY)
        return output.getvalue(), True
    except Exception:
        return file_data, False

def upload_to_backblaze(file):
    """
    Subir archivo a Backblaze B2 Storage
    
    Args:
        file: Archivo de Werkzeug FileStorage
        
    Returns:
        dict: Diccionario con success, message, y file_url (si es exitoso)
    """
    try:
        # Verificar que el bucket esté disponible
        if bucket is None:
            return {
                'success': False,
                'message': 'Backblaze B2 no está disponible',
                'file_url': None
            }
        
        # Verificar que el archivo existe
        if not file or not file.filename:
            return {
                'success': False,
                'message': 'No se proporcionó ningún archivo',
                'file_url': None
            }
        
        # Verificar extensiones permitidas
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return {
                'success': False,
                'message': f'Extensión de archivo no permitida. Permitidas: {", ".join(allowed_extensions)}',
                'file_url': None
            }
        
        # Leer datos del archivo
        file.seek(0)  # Asegurar que estamos al inicio del archivo
        file_data = file.read()

        # Verificar tamaño del archivo original (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_data) > max_size:
            return {
                'success': False,
                'message': 'El archivo es demasiado grande. Máximo 10MB',
                'file_url': None
            }

        # Convertir a WebP para reducir el peso de la imagen
        file_data, converted = convert_to_webp(file_data, file_ext)

        # Generar nombre único para el archivo
        unique_id = str(uuid.uuid4())[:8]
        base_name = os.path.splitext(filename)[0]
        if converted:
            unique_filename = f"images/{unique_id}_{base_name}.webp"
            content_type = 'image/webp'
        else:
            unique_filename = f"images/{unique_id}_{filename}"
            content_type = file.content_type or 'application/octet-stream'

        # Subir archivo a Backblaze B2
        uploaded_file = bucket.upload_bytes(
            data_bytes=file_data,
            file_name=unique_filename,
            content_type=content_type
        )
        
        # Obtener la URL pública del archivo
        file_url = bucket.get_download_url(unique_filename)
        
        Logger.add_to_log("info", f"Archivo subido exitosamente: {unique_filename}")
        
        return {
            'success': True,
            'message': 'Archivo subido exitosamente',
            'file_url': file_url,
            'filename': unique_filename
        }
        
    except Exception as e:
        error_msg = f"Error subiendo archivo a Backblaze: {str(e)}"
        Logger.add_to_log("error", error_msg)
        Logger.add_to_log("error", traceback.format_exc())
        
        return {
            'success': False,
            'message': 'Error interno del servidor al subir archivo',
            'file_url': None
        }
