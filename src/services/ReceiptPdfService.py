import io
import traceback
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle)

# Logger
from src.utils.Logger import Logger
# Services
from src.services.UtilityBillingService import UtilityBillingService

# Paleta alineada con el panel de administracion
INK = colors.HexColor('#111827')
MUTED = colors.HexColor('#6B7280')
LINE = colors.HexColor('#E5E7EB')
SOFT = colors.HexColor('#F9FAFB')
ACCENT = colors.HexColor('#2563EB')
GREEN = colors.HexColor('#059669')

MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
          'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']


def period_label(period):
    """'2026-03' -> 'Marzo 2026'"""
    if not period or len(period) < 7:
        return period or ''
    try:
        return '%s %s' % (MONTHS[int(period[5:7]) - 1], period[:4])
    except (ValueError, IndexError):
        return period


def fecha(value):
    """Formatea una fecha a dd-mm-aaaa. Acepta 'YYYY-MM-DD', date o None."""
    if not value:
        return ''
    text = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    parts = text[:10].split('-')
    if len(parts) == 3 and len(parts[0]) == 4:
        return '%s-%s-%s' % (parts[2], parts[1], parts[0])
    return text


def soles(value):
    return 'S/ %s' % format(Decimal(str(value or 0)).quantize(Decimal('0.01')), ',.2f')


def number(value, places='0.01'):
    """Formatea con los decimales que indique `places` ('0.01', '0.0001', ...)."""
    quantum = Decimal(places)
    decimals = max(-quantum.as_tuple().exponent, 0)
    return format(Decimal(str(value or 0)).quantize(quantum), ',.%df' % decimals)


class ReceiptPdfService():
    """Genera el PDF del recibo de servicios de un departamento.

    Reemplaza la captura de pantalla del Excel que se enviaba por WhatsApp.
    """

    @classmethod
    def _styles(cls):
        base = getSampleStyleSheet()
        return {
            'title': ParagraphStyle('t', parent=base['Normal'], fontName='Helvetica-Bold',
                                    fontSize=17, textColor=INK, leading=21),
            'sub': ParagraphStyle('s', parent=base['Normal'], fontName='Helvetica',
                                  fontSize=9.5, textColor=MUTED, leading=13),
            'section': ParagraphStyle('sec', parent=base['Normal'], fontName='Helvetica-Bold',
                                      fontSize=8.5, textColor=MUTED, leading=12,
                                      spaceBefore=14, spaceAfter=5),
            'note': ParagraphStyle('n', parent=base['Normal'], fontName='Helvetica',
                                   fontSize=7.5, textColor=MUTED, leading=11),
        }

    @classmethod
    def build_receipt(cls, charge_id):
        """Devuelve (bytes_pdf, nombre_archivo) o (None, None) si falla."""
        try:
            detail = UtilityBillingService.get_charge_detail(charge_id)
            if not detail:
                return None, None

            styles = cls._styles()
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer, pagesize=A4,
                leftMargin=20 * mm, rightMargin=20 * mm,
                topMargin=18 * mm, bottomMargin=18 * mm,
                title='Recibo %s %s' % (detail.get('unit_code'), detail.get('period')),
                author='Amarutech')

            story = []

            # Encabezado
            header = Table([[
                Paragraph('Recibo de servicios', styles['title']),
                Paragraph('Departamento <b>%s</b><br/>%s'
                          % (detail.get('unit_code') or '-',
                             period_label(detail.get('period'))), styles['sub']),
            ]], colWidths=[100 * mm, 70 * mm])
            header.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LINEBELOW', (0, 0), (-1, -1), 1, ACCENT),
            ]))
            story.append(header)
            story.append(Spacer(1, 12))

            # Datos del inquilino
            period_range = ''
            if detail.get('period_start') and detail.get('period_end'):
                period_range = '%s al %s' % (fecha(detail['period_start']),
                                             fecha(detail['period_end']))

            info = Table([
                ['Inquilino', detail.get('tenant_name') or '—'],
                ['Periodo', period_range or period_label(detail.get('period'))],
            ], colWidths=[35 * mm, 135 * mm])
            info.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica-Bold', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
                ('TEXTCOLOR', (1, 0), (1, -1), INK),
                ('BACKGROUND', (0, 0), (-1, -1), SOFT),
                ('LEFTPADDING', (0, 0), (-1, -1), 9),
                ('RIGHTPADDING', (0, 0), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(info)

            # Lecturas
            readings = detail.get('readings') or []
            if readings:
                story.append(Paragraph('LECTURAS', styles['section']))
                # Se muestran las fechas de cada lectura: el ciclo de facturacion
                # va de toma a toma y no coincide con el mes calendario.
                rows = [['Medidor', 'Desde', 'Hasta', 'Anterior', 'Actual', 'Consumo']]
                for r in readings:
                    rows.append([
                        r.get('meter_code') or '—',
                        fecha(r.get('previous_date')) or '—',
                        fecha(r.get('current_date')) or '—',
                        '%s KW' % number(r.get('previous_reading')),
                        '%s KW' % number(r.get('current_reading')),
                        '%s KW' % number(r.get('consumption')),
                    ])
                # Con varios medidores conviene ver el total sumado
                if len(readings) > 1:
                    rows.append(['Total', '', '', '', '',
                                 '%s KW' % number(detail.get('electricity_consumption'))])

                table = Table(rows, colWidths=[26 * mm, 27 * mm, 27 * mm,
                                               30 * mm, 30 * mm, 30 * mm])
                style = [
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 7.5),
                    ('FONT', (0, 1), (-1, -1), 'Helvetica', 8.5),
                    ('TEXTCOLOR', (0, 0), (-1, 0), MUTED),
                    ('TEXTCOLOR', (1, 1), (2, -1), MUTED),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('LINEBELOW', (0, 0), (-1, 0), 0.6, LINE),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, SOFT]),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]
                if len(readings) > 1:
                    style += [('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 8.5),
                              ('LINEABOVE', (0, -1), (-1, -1), 0.6, LINE),
                              ('BACKGROUND', (0, -1), (-1, -1), colors.white)]
                table.setStyle(TableStyle(style))
                story.append(table)

            # Conceptos
            story.append(Paragraph('CONCEPTOS', styles['section']))
            concepts = [['Concepto', 'Detalle', 'Importe']]

            # La tarifa va con 4 decimales: redondeada a 2 daria 'S/ 1.00' y el
            # inquilino no podria rehacer la multiplicacion.
            concepts.append([
                'Luz',
                '%s KW x S/ %s' % (number(detail.get('electricity_consumption')),
                                   number(detail.get('electricity_price'), '0.0001')),
                soles(detail.get('electricity_amount')),
            ])
            # Un cargo con tarifa plana se guarda sin personas: mostrar el
            # prorrateo ahi diria '0 persona(s) x S/ 0.00' y no cuadraria con
            # el importe cobrado.
            water_flat = (not detail.get('water_people')
                          and Decimal(str(detail.get('water_amount') or 0)) > 0)
            if water_flat:
                water_note = 'Tarifa plana mensual'
            else:
                water_note = '%s persona(s) x %s' % (detail.get('water_people') or 0,
                                                     soles(detail.get('water_price')))
            concepts.append(['Agua', water_note, soles(detail.get('water_amount'))])
            if detail.get('internet_amount'):
                concepts.append(['Internet', 'Monto fijo mensual',
                                 soles(detail.get('internet_amount'))])
            if detail.get('previous_credit'):
                concepts.append(['Saldo a favor', 'Del periodo anterior',
                                 '- %s' % soles(detail.get('previous_credit'))])

            concepts.append(['Total a pagar', '', soles(detail.get('total_amount'))])

            table = Table(concepts, colWidths=[38 * mm, 88 * mm, 44 * mm])
            style = [
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
                ('FONT', (0, 1), (-1, -2), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (-1, 0), MUTED),
                ('TEXTCOLOR', (1, 1), (1, -2), MUTED),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('LINEBELOW', (0, 0), (-1, 0), 0.6, LINE),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                # Fila del total
                ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 11),
                ('TEXTCOLOR', (0, -1), (-1, -1), ACCENT),
                ('LINEABOVE', (0, -1), (-1, -1), 1, ACCENT),
                ('TOPPADDING', (0, -1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 9),
            ]
            if detail.get('previous_credit'):
                style.append(('TEXTCOLOR', (2, -2), (2, -2), GREEN))
            table.setStyle(TableStyle(style))
            story.append(table)

            # Estado de pago
            paid = Decimal(str(detail.get('paid_amount') or 0))
            total = Decimal(str(detail.get('total_amount') or 0))
            if paid > 0:
                story.append(Paragraph('PAGOS', styles['section']))
                rows = [['Fecha', 'Método', 'Importe']]
                for p in (detail.get('payments') or []):
                    rows.append([p.get('payment_date') or '—',
                                 (p.get('method') or '—').capitalize(),
                                 soles(p.get('amount'))])
                rows.append(['Pendiente', '', soles(total - paid)])

                table = Table(rows, colWidths=[55 * mm, 71 * mm, 44 * mm])
                table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
                    ('FONT', (0, 1), (-1, -2), 'Helvetica', 9),
                    ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 9),
                    ('TEXTCOLOR', (0, 0), (-1, 0), MUTED),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                    ('LINEBELOW', (0, 0), (-1, 0), 0.6, LINE),
                    ('LINEABOVE', (0, -1), (-1, -1), 0.6, LINE),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(table)

            if detail.get('credit_balance'):
                story.append(Spacer(1, 8))
                story.append(Paragraph(
                    'Saldo a favor de %s que se descuenta del próximo recibo.'
                    % soles(detail.get('credit_balance')), styles['note']))

            story.append(Spacer(1, 18))
            nota = ('La tarifa por KW sale del total del recibo de luz del edificio '
                    'dividido entre el total de KW consumidos. ')
            if water_flat:
                nota += 'El agua se cobra con la tarifa plana mensual acordada.'
            else:
                nota += ('La tarifa por persona del agua sale del total del recibo '
                         'dividido entre el total de personas.')
            story.append(Paragraph(nota, styles['note']))

            doc.build(story)
            pdf = buffer.getvalue()
            buffer.close()

            filename = 'recibo-%s-%s.pdf' % (detail.get('unit_code') or 'depto',
                                             detail.get('period') or '')
            return pdf, filename
        except Exception as ex:
            Logger.add_to_log("error", f"Error generando PDF del recibo: {str(ex)}")
            Logger.add_to_log("error", traceback.format_exc())
            return None, None
