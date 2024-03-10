from decouple import config

import psycopg
import traceback

# Logger
from src.utils.Logger import Logger


def get_connection():
    try:
        return psycopg.connect(
            host=config('POSTGRES_HOST'),
            user=config('POSTGRES_USER'),
            password=config('POSTGRES_PASSWORD'),
            dbname=config('POSTGRES_DATABASE')
            
            
        )
    except Exception as ex:
        Logger.add_to_log("error", str(ex))
        Logger.add_to_log("error", traceback.format_exc())