from decouple import config

import psycopg
import traceback

# Logger
from src.utils.Logger import Logger


def get_connection():
    try:
        return psycopg.connect(
            host=config('PGSQL_HOST'),
            user=config('PGSQL_USER'),
            password=config('PGSQL_PASSWORD'),
            dbname=config('PGSQL_DB')
        )
    except Exception as ex:
        Logger.add_to_log("error", str(ex))
        Logger.add_to_log("error", traceback.format_exc())