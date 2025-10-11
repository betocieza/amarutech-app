import os
import traceback
import uuid
from werkzeug.utils import secure_filename
from src.database.b2_connection import bucket, b2_api
from src.utils.Logger import Logger

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
        
        # Generar nombre único para el archivo
        unique_id = str(uuid.uuid4())[:8]
        unique_filename = f"images/{unique_id}_{filename}"
        
        # Leer datos del archivo
        file.seek(0)  # Asegurar que estamos al inicio del archivo
        file_data = file.read()
        
        # Verificar tamaño del archivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_data) > max_size:
            return {
                'success': False,
                'message': 'El archivo es demasiado grande. Máximo 10MB',
                'file_url': None
            }
        
        # Subir archivo a Backblaze B2
        uploaded_file = bucket.upload_bytes(
            data_bytes=file_data,
            file_name=unique_filename,
            content_type=file.content_type or 'application/octet-stream'
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
