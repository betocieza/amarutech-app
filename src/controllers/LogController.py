import os
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

# Security
from src.utils.Logger import Logger
from src.utils.Security import Security

main = Blueprint('log_blueprint', __name__)

@main.route('/list', methods=['GET'])
def get_logs():
    """Obtener logs del sistema - requiere autenticación"""
   #has_access = Security.verify_token(request.headers)
    
   #if not has_access:
     #   return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        # Parámetros de consulta
        lines = request.args.get('lines', 100, type=int)  # Número de líneas
        level = request.args.get('level', 'all')  # Filtro por nivel: info, error, warning, all
        date_from = request.args.get('date_from')  # Fecha desde (YYYY-MM-DD)
        date_to = request.args.get('date_to')  # Fecha hasta (YYYY-MM-DD)
        search = request.args.get('search', '')  # Búsqueda en contenido
        
        # Validar límites
        if lines > 1000:
            lines = 1000
        if lines < 1:
            lines = 100
            
        # Ruta del archivo de log
        log_file_path = os.path.join('src', 'utils', 'log', 'app.log')
        
        if not os.path.exists(log_file_path):
            return jsonify({
                'message': 'Archivo de log no encontrado',
                'success': False
            }), 404
        
        # Leer logs
        logs = []
        try:
            with open(log_file_path, 'r', encoding='utf-8') as file:
                all_lines = file.readlines()
                
                # Obtener las últimas N líneas
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Parsear línea de log
                    log_entry = parse_log_line(line)
                    if log_entry:
                        # Aplicar filtros
                        if level != 'all' and log_entry['level'].lower() != level.lower():
                            continue
                            
                        if date_from and log_entry['date'] < date_from:
                            continue
                            
                        if date_to and log_entry['date'] > date_to:
                            continue
                            
                        if search and search.lower() not in log_entry['message'].lower():
                            continue
                            
                        logs.append(log_entry)
        
        except Exception as file_ex:
            Logger.add_to_log("error", f"Error leyendo archivo de log: {str(file_ex)}")
            return jsonify({
                'message': 'Error leyendo archivo de log',
                'success': False
            }), 500
        
        # Estadísticas de logs
        stats = get_log_stats(logs)
        
        return jsonify({
            'success': True,
            'data': logs,
            'total': len(logs),
            'stats': stats,
            'filters': {
                'lines': lines,
                'level': level,
                'date_from': date_from,
                'date_to': date_to,
                'search': search
            }
        }), 200
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo logs: {str(ex)}")
        Logger.add_to_log("error", traceback.format_exc())
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/logs/download', methods=['GET'])
def download_logs():
    """Descargar archivo de logs completo - requiere autenticación"""
    has_access = Security.verify_token(request.headers)
    
    if not has_access:
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        log_file_path = os.path.join('src', 'utils', 'log', 'app.log')
        
        if not os.path.exists(log_file_path):
            return jsonify({
                'message': 'Archivo de log no encontrado',
                'success': False
            }), 404
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f'app_logs_{timestamp}.log'
        
        return send_file(
            log_file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='text/plain'
        )
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error descargando logs: {str(ex)}")
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/logs/clear', methods=['POST'])
def clear_logs():
    """Limpiar archivo de logs - requiere autenticación"""
    has_access = Security.verify_token(request.headers)
    
    if not has_access:
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        log_file_path = os.path.join('src', 'utils', 'log', 'app.log')
        
        if not os.path.exists(log_file_path):
            return jsonify({
                'message': 'Archivo de log no encontrado',
                'success': False
            }), 404
        
        # Crear respaldo antes de limpiar
        backup_path = log_file_path.replace('.log', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        with open(log_file_path, 'r', encoding='utf-8') as original:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(original.read())
        
        # Limpiar archivo principal
        with open(log_file_path, 'w', encoding='utf-8') as file:
            file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | INFO | Log file cleared by admin\n")
        
        Logger.add_to_log("info", f"Archivo de log limpiado. Respaldo creado en: {backup_path}")
        
        return jsonify({
            'message': 'Archivo de log limpiado exitosamente',
            'success': True,
            'backup_file': backup_path
        }), 200
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error limpiando logs: {str(ex)}")
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/logs/stats', methods=['GET'])
def get_logs_stats():
    """Obtener estadísticas de logs - requiere autenticación"""
    has_access = Security.verify_token(request.headers)
    
    if not has_access:
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        log_file_path = os.path.join('src', 'utils', 'log', 'app.log')
        
        if not os.path.exists(log_file_path):
            return jsonify({
                'message': 'Archivo de log no encontrado',
                'success': False
            }), 404
        
        # Obtener información del archivo
        file_stats = os.stat(log_file_path)
        file_size = file_stats.st_size
        last_modified = datetime.fromtimestamp(file_stats.st_mtime)
        
        # Contar líneas y niveles
        total_lines = 0
        levels_count = {'INFO': 0, 'ERROR': 0, 'WARNING': 0, 'DEBUG': 0}
        recent_errors = []
        
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            total_lines = len(lines)
            
            # Analizar últimas 1000 líneas
            recent_lines = lines[-1000:] if len(lines) > 1000 else lines
            
            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue
                    
                log_entry = parse_log_line(line)
                if log_entry:
                    level = log_entry['level'].upper()
                    if level in levels_count:
                        levels_count[level] += 1
                    
                    # Recopilar errores recientes
                    if level == 'ERROR' and len(recent_errors) < 10:
                        recent_errors.append(log_entry)
        
        return jsonify({
            'success': True,
            'stats': {
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'total_lines': total_lines,
                'last_modified': last_modified.isoformat(),
                'levels_count': levels_count,
                'recent_errors': recent_errors,
                'error_rate': round((levels_count['ERROR'] / max(sum(levels_count.values()), 1)) * 100, 2)
            }
        }), 200
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo estadísticas: {str(ex)}")
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


@main.route('/logs/live', methods=['GET'])
def get_live_logs():
    """Obtener logs en tiempo real (últimas 50 líneas) - para dashboard"""
    has_access = Security.verify_token(request.headers)
    
    if not has_access:
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        log_file_path = os.path.join('src', 'utils', 'log', 'app.log')
        
        if not os.path.exists(log_file_path):
            return jsonify({
                'message': 'Archivo de log no encontrado',
                'success': False
            }), 404
        
        # Obtener últimas 50 líneas
        logs = []
        with open(log_file_path, 'r', encoding='utf-8') as file:
            all_lines = file.readlines()
            recent_lines = all_lines[-50:] if len(all_lines) > 50 else all_lines
            
            for line in recent_lines:
                line = line.strip()
                if line:
                    log_entry = parse_log_line(line)
                    if log_entry:
                        logs.append(log_entry)
        
        # Estadísticas rápidas
        quick_stats = {
            'total_recent': len(logs),
            'errors_count': len([log for log in logs if log['level'].upper() == 'ERROR']),
            'warnings_count': len([log for log in logs if log['level'].upper() == 'WARNING']),
            'last_update': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': logs,
            'stats': quick_stats
        }), 200
        
    except Exception as ex:
        Logger.add_to_log("error", f"Error obteniendo logs en vivo: {str(ex)}")
        return jsonify({
            'message': 'Error interno del servidor',
            'success': False
        }), 500


# Funciones auxiliares
def parse_log_line(line):
    """Parsear una línea de log y extraer información"""
    try:
        # Formato esperado: 2025-10-07 16:41:09 | INFO | Mensaje
        parts = line.split(' | ')
        if len(parts) >= 3:
            date_time = parts[0].strip()
            level = parts[1].strip()
            message = ' | '.join(parts[2:]).strip()
            
            return {
                'datetime': date_time,
                'date': date_time.split(' ')[0] if ' ' in date_time else date_time,
                'time': date_time.split(' ')[1] if ' ' in date_time else '',
                'level': level,
                'message': message,
                'raw_line': line
            }
    except Exception:
        pass
    
    # Si no se puede parsear, devolver como mensaje genérico
    return {
        'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'level': 'UNKNOWN',
        'message': line,
        'raw_line': line
    }


def get_log_stats(logs):
    """Obtener estadísticas de una lista de logs"""
    if not logs:
        return {
            'total': 0,
            'by_level': {},
            'by_date': {},
            'recent_errors': []
        }
    
    by_level = {}
    by_date = {}
    recent_errors = []
    
    for log in logs:
        # Contar por nivel
        level = log['level']
        by_level[level] = by_level.get(level, 0) + 1
        
        # Contar por fecha
        date = log['date']
        by_date[date] = by_date.get(date, 0) + 1
        
        # Recopilar errores recientes
        if level.upper() == 'ERROR' and len(recent_errors) < 5:
            recent_errors.append(log)
    
    return {
        'total': len(logs),
        'by_level': by_level,
        'by_date': by_date,
        'recent_errors': recent_errors
    }