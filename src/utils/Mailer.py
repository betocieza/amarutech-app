import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from decouple import config

from src.utils.Logger import Logger


class Mailer():

    host = config('SMTP_HOST', default='smtp.zoho.com')
    port = config('SMTP_PORT', default=587, cast=int)
    user = config('SMTP_USER', default='')
    password = config('SMTP_PASSWORD', default='')
    sender_name = config('SMTP_SENDER_NAME', default='Amarutech')

    @classmethod
    def send_password_reset_email(cls, to_email, reset_url):
        subject = 'Recupera tu contraseña - Amarutech'
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
            <h2>Recupera tu contraseña</h2>
            <p>Recibimos una solicitud para restablecer tu contraseña. Haz clic en el siguiente botón para continuar:</p>
            <p style="text-align: center; margin: 24px 0;">
                <a href="{reset_url}" style="background:#2563eb;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;">
                    Restablecer contraseña
                </a>
            </p>
            <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>Este enlace expira en 1 hora. Si no solicitaste este cambio, puedes ignorar este correo.</p>
        </div>
        """

        return cls._send(to_email, subject, html_body)

    @classmethod
    def _send(cls, to_email, subject, html_body):
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{cls.sender_name} <{cls.user}>"
            message['To'] = to_email
            message.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP(cls.host, cls.port) as server:
                server.starttls()
                server.login(cls.user, cls.password)
                server.sendmail(cls.user, to_email, message.as_string())

            return True
        except Exception as ex:
            Logger.add_to_log("error", f"Error enviando email: {str(ex)}")
            Logger.add_to_log("error", traceback.format_exc())
            return False
