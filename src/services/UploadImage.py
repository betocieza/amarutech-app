import os
import traceback
from werkzeug.utils import secure_filename
from src.database.b2_connection import bucket

def upload_to_backblaze(file):
    try:
      
        # Asegurar un nombre de archivo único
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{os.urandom(8).hex()}{file_ext}"

        # Subir archivo a Backblaze
        file_data = file.stream.read()
        uploaded_file = bucket.upload_bytes(data_bytes=file_data,file_name=unique_filename)

        # Obtener la URL pública del archivo
        #file_url = f"https://f002.backblazeb2.com/file/{B2_BUCKET_NAME}/{unique_filename}"
        #response=bucket.upload_bytes(data_bytes=image,file_name=file_name)
        file_url = bucket.get_download_url(unique_filename)

        return file_url
    except Exception as e:
        print("Error uploading to Backblaze:", str(e))
        print(traceback.format_exc())
        return None
