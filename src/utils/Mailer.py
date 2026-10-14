import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

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
    def send_receipt_email(cls, to_email, charge, pdf_bytes=None, pdf_name=None):
        """Envía el recibo de servicios al inquilino, con el PDF adjunto."""
        unit = charge.get('unit_code') or ''
        period = charge.get('period') or ''
        tenant = charge.get('tenant_name') or ''
        total = charge.get('total_amount') or 0

        subject = 'Recibo de servicios %s - Depto. %s' % (period, unit)

        rows = [
            ('Luz', charge.get('electricity_amount') or 0),
            ('Agua', charge.get('water_amount') or 0),
        ]
        if charge.get('internet_amount'):
            rows.append(('Internet', charge.get('internet_amount')))

        detail_html = ''.join(
            '<tr><td style="padding:7px 0;color:#6B7280;">%s</td>'
            '<td style="padding:7px 0;text-align:right;">S/ %.2f</td></tr>'
            % (label, float(amount)) for label, amount in rows)

        if charge.get('previous_credit'):
            detail_html += (
                '<tr><td style="padding:7px 0;color:#6B7280;">Saldo a favor anterior</td>'
                '<td style="padding:7px 0;text-align:right;color:#059669;">- S/ %.2f</td></tr>'
                % float(charge['previous_credit']))

        html_body = """
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; color:#111827;">
            <h2 style="margin:0 0 4px;">Recibo de servicios</h2>
            <p style="margin:0 0 20px;color:#6B7280;">Departamento %s &middot; %s</p>
            <p>Hola%s,</p>
            <p>Este es el detalle de tus servicios del periodo:</p>
            <table style="width:100%%;border-collapse:collapse;font-size:14px;">
                %s
                <tr>
                    <td style="padding:12px 0 0;border-top:2px solid #2563eb;font-weight:bold;">Total a pagar</td>
                    <td style="padding:12px 0 0;border-top:2px solid #2563eb;text-align:right;font-weight:bold;color:#2563eb;font-size:17px;">S/ %.2f</td>
                </tr>
            </table>
            %s
            <p style="color:#6B7280;font-size:12px;margin-top:24px;">
                La tarifa por KW sale del total del recibo de luz del edificio dividido entre
                el total de KW consumidos. La tarifa por persona del agua sale del total del
                recibo dividido entre el total de personas.
            </p>
        </div>
        """ % (unit, period,
               ' ' + tenant.split()[0].capitalize() if tenant else '',
               detail_html, float(total),
               '<p style="color:#6B7280;font-size:13px;margin-top:18px;">'
               'Adjuntamos el recibo detallado en PDF.</p>' if pdf_bytes else '')

        attachments = [(pdf_name or 'recibo.pdf', pdf_bytes, 'pdf')] if pdf_bytes else None
        return cls._send(to_email, subject, html_body, attachments=attachments)

    @classmethod
    def _send(cls, to_email, subject, html_body, attachments=None):
        """Envía un correo. `attachments` es una lista de (nombre, bytes, mime_subtype)."""
        try:
            # Con adjuntos el contenedor debe ser 'mixed': 'alternative' es para
            # versiones del mismo cuerpo, no para archivos.
            if attachments:
                message = MIMEMultipart('mixed')
                body = MIMEMultipart('alternative')
                body.attach(MIMEText(html_body, 'html'))
                message.attach(body)
            else:
                message = MIMEMultipart('alternative')
                message.attach(MIMEText(html_body, 'html'))

            message['Subject'] = subject
            message['From'] = f"{cls.sender_name} <{cls.user}>"
            message['To'] = to_email

            for filename, content, subtype in (attachments or []):
                part = MIMEApplication(content, _subtype=subtype)
                part.add_header('Content-Disposition', 'attachment', filename=filename)
                message.attach(part)

            with smtplib.SMTP(cls.host, cls.port) as server:
                server.starttls()
                server.login(cls.user, cls.password)
                server.sendmail(cls.user, to_email, message.as_string())

            return True
        except Exception as ex:
            Logger.add_to_log("error", f"Error enviando email: {str(ex)}")
            Logger.add_to_log("error", traceback.format_exc())
            return False
