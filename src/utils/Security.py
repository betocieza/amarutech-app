from decouple import config

import datetime
import jwt
import pytz
import traceback

# Logger
from src.utils.Logger import Logger


class Security():

    secret = config('JWT_KEY')
    tz = pytz.timezone("America/Lima")

    @classmethod
    def generate_token(cls, authenticated_user):
        try:
            payload = {
                'iat': datetime.datetime.now(tz=cls.tz),
                'exp': datetime.datetime.now(tz=cls.tz) + datetime.timedelta(minutes=240),
                'user_id':authenticated_user.user_id,
                'username': authenticated_user.username,
                'first_name': authenticated_user.first_name,
                'roles': ['Administrator', 'Editor']
            }
            return jwt.encode(payload, cls.secret, algorithm="HS256")
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())

    @classmethod
    def verify_token(cls, headers):
        try:
            if 'Authorization' in headers.keys():
                authorization = headers['Authorization']              
                encoded_token = authorization.split(" ")[1]
              
                if (len(encoded_token) > 0) :
                    try:
                        payload = jwt.decode(encoded_token, cls.secret, algorithms=["HS256"])
                        roles = list(payload['roles'])

                        if 'Administrator' in roles:
                            return True
                        return False
                    except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
                        return False
            return False
        except Exception as ex:
            Logger.add_to_log("error", str(ex))
            Logger.add_to_log("error", traceback.format_exc())