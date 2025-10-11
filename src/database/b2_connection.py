from decouple import config
import b2sdk.v2 as b2

# Configuración de B2 con claves reales
info = b2.InMemoryAccountInfo()
b2_api = b2.B2Api(info)

application_key_id = config("B2_KEY_ID")
application_key = config("B2_APP_KEY")
bucket_name = config("B2_BUCKET_NAME")

try:
    b2_api.authorize_account("production", application_key_id, application_key)
    bucket = b2_api.get_bucket_by_name(bucket_name)
    print(f"Conectado exitosamente a B2 bucket: {bucket_name}")
except Exception as e:
    print(f"Error conectando a B2: {str(e)}")
    bucket = None

#print("Test",bucket)
