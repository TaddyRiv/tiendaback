import openai
import io
from django.conf import settings
import json
from datetime import datetime, timedelta
from django.utils import timezone

# Configurar OpenAI
openai.api_key = settings.OPENAI_API_KEY


class ReportesIAService:
    """Servicio para interpretar peticiones de reportes con IA"""
    
    def __init__(self):
        self.modelo = "gpt-4-turbo-preview"  # o "gpt-3.5-turbo" para más económico
    
    def transcribir_audio(self, audio_file):
        """
        Convierte audio a texto usando Whisper de OpenAI
        """
        try:
            #  Validar que el archivo tenga tamaño suficiente
            if audio_file.size < 1000:
                return {'error': 'Archivo de audio vacío o demasiado pequeño'}

            print(" Recibido para transcripción:", audio_file.name, audio_file.content_type, audio_file.size)

            # Preparar el 'file' en el formato que espera openai-python.
            # openai acepta: bytes, io.IOBase, PathLike o un tuple (filename, fileobj, content_type).
            file_param = None

            # Si el upload está guardado en disco (TemporaryUploadedFile), usa la ruta
            temp_path = getattr(audio_file, 'temporary_file_path', None)
            if callable(temp_path):
                try:
                    path = audio_file.temporary_file_path()
                    file_param = path
                except Exception:
                    file_param = None

            # Si tenemos un objeto file interno (InMemoryUploadedFile.file), úsalo (asegurando rewind)
            if file_param is None and hasattr(audio_file, 'file'):
                file_obj = audio_file.file
                try:
                    # Intentar hacer seek al inicio si es posible
                    if hasattr(file_obj, 'seek'):
                        file_obj.seek(0)
                except Exception:
                    pass

                # Pasar como tuple (nombre, fileobj, content_type)
                file_param = (audio_file.name, file_obj, getattr(audio_file, 'content_type', None))

            # Como fallback, leer bytes y envolver en BytesIO
            if file_param is None:
                try:
                    audio_bytes = audio_file.read()
                    bio = io.BytesIO(audio_bytes)
                    bio.seek(0)
                    file_param = (getattr(audio_file, 'name', 'audio'), bio, getattr(audio_file, 'content_type', 'audio/webm'))
                except Exception as e:
                    return {'error': f'No se pudo procesar el archivo de audio: {str(e)}'}

            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=file_param,
                language="es"
            )

            # openai-python puede devolver un dict o un objeto con atributo .text
            if hasattr(transcript, 'text'):
                return transcript.text
            if isinstance(transcript, dict):
                return transcript.get('text') or transcript
            return transcript

        except Exception as e:
            print("❌ Error Whisper:", e)
            return {'error': f'Error al transcribir audio: {str(e)}'}

    
    def interpretar_solicitud(self, texto_usuario):
        """
        Interpreta la solicitud del usuario y genera parámetros para el generador
        
        Args:
            texto_usuario: Texto de la solicitud (ej: "ventas de enero")
        
        Returns:
            dict: Parámetros estructurados para el generador
        """
        
        # Fecha de hoy para contexto
        hoy = timezone.now().date()
        
        # Prompt para ChatGPT
        prompt = f"""
Eres un asistente que convierte solicitudes de reportes en lenguaje natural a parámetros estructurados.

FECHA DE HOY: {hoy.strftime('%Y-%m-%d')}

MODELOS DISPONIBLES:
- ventas: Tabla de ventas (SalesNote)
- detalles: Detalles de ventas por producto (DetailNote)
- productos: Productos (Product)
- clientes: Clientes/Usuarios (Usuario)
- creditos: Ventas a crédito (CreditSale)

CAMPOS IMPORTANTES:
- ventas: fecha, monto, tipo_pago (contado/credito), empleado, cliente
- detalles: cantidad, subtotal, producto, nota (venta)
- productos: nombre, categoria, precio, stock
- clientes: email, first_name, compras_realizadas, total_gastado

TIPOS DE REPORTES PREDEFINIDOS (si aplica):
1. "ventas_periodo" - Ventas entre fechas
2. "top_productos" - Productos más vendidos
3. "bajo_stock" - Productos con poco inventario
4. "rfm" - Análisis de clientes
5. "flujo_caja" - Análisis de pagos
6. "cartera_creditos" - Estado de créditos
7. "dashboard" - Dashboard completo

SOLICITUD DEL USUARIO:
"{texto_usuario}"

INSTRUCCIONES:
1. Si es un reporte predefinido, devuelve: {{"tipo": "predefinido", "reporte": "nombre_reporte", "parametros": {{...}}}}
2. Si es un reporte personalizado, devuelve: {{"tipo": "dinamico", "config": {{...}}}}

Para reportes dinámicos usa esta estructura:
{{
  "tipo": "dinamico",
  "config": {{
    "modelo": "ventas|detalles|productos|clientes",
    "filtros": {{
      "campo__operador": "valor"
    }},
    "agrupar_por": ["campo1", "campo2", "campo3", "campo4"],
    "metricas": {{
      "nombre_metrica": {{"tipo": "sum|count|avg|max|min", "campo": "nombre_campo"}}
    }},
    "ordenar_por": ["-campo"]
  }},
  "descripcion_humana": "Descripción de lo que se calculó"
}}

OPERADORES DE FECHA:
- "gte" para mayor o igual (desde)
- "lte" para menor o igual (hasta)
- "month" para filtrar por mes
- "year" para filtrar por año

EJEMPLOS DE CONVERSIÓN CON RELACIONES:

Usuario: "dame los 3 productos menos vendidos con sus respectivos nombres"
Respuesta: {{
    "tipo": "dinamico",
    "config": {{
        "modelo": "detalles",
        "filtros": {{ }},
        "agrupar_por": ["producto__id", "producto__nombre", "producto__precio"],
        "metricas": {{
            "cantidad_vendida": {{"tipo": "sum", "campo": "cantidad"}}
        }},
        "ordenar_por": ["cantidad_vendida"],
        "limite": 3
    }},
    "descripcion_humana": "Los 3 productos menos vendidos con sus nombres y precios"
}}

Usuario: "productos por categoría con ventas totales"
Respuesta: {{
    "tipo": "dinamico",
    "config": {{
        "modelo": "detalles",
        "filtros": {{ }},
        "agrupar_por": ["producto__categoria__descripcion"],
        "metricas": {{
            "unidades": {{"tipo": "sum", "campo": "cantidad"}},
            "ingresos": {{"tipo": "sum", "campo": "subtotal"}}
        }},
        "ordenar_por": ["-ingresos"]
    }},
    "descripcion_humana": "Productos agrupados por categoría con ventas e ingresos"
}}

Usuario: "clientes con más compras y su email"
Respuesta: {{
    "tipo": "dinamico",
    "config": {{
        "modelo": "ventas",
        "filtros": {{ }},
        "agrupar_por": ["cliente__id", "cliente__email", "cliente__first_name"],
        "metricas": {{
            "total_compras": {{"tipo": "count", "campo": "id"}},
            "total_gastado": {{"tipo": "sum", "campo": "monto"}}
        }},
        "ordenar_por": ["-total_compras"],
        "limite": 10
    }},
    "descripcion_humana": "Top 10 clientes con más compras"
}}

REGLAS IMPORTANTES PARA AGRUPAR:
1. Siempre incluir el ID cuando agrupes por una entidad relacionada
2. Para acceder a campos relacionados usa __ (doble guión bajo)
3. Ejemplos:
     - producto__nombre (nombre del producto)
     - producto__categoria__descripcion (categoría del producto)
     - cliente__email (email del cliente)
     - empleado__first_name (nombre del empleado)
4. Si piden "con sus nombres", SIEMPRE incluir los campos de nombre/descripción
5. Usar "limite" cuando pidan "top X", "los X más/menos", "primeros X"

RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL.
"""

        try:
            response = openai.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en análisis de datos y reportes de ventas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Baja temperatura para respuestas más precisas
                response_format={"type": "json_object"}
            )
            
            resultado = json.loads(response.choices[0].message.content)
            return resultado
            
        except json.JSONDecodeError as e:
            return {
                'error': 'Error al parsear respuesta de IA',
                'detalle': str(e)
            }
        except Exception as e:
            return {
                'error': f'Error en IA: {str(e)}'
            }
    
    def generar_respuesta_natural(self, datos_reporte, descripcion_reporte):
        """
        Convierte los datos del reporte en una respuesta en lenguaje natural
        
        Args:
            datos_reporte: Resultado del generador de reportes
            descripcion_reporte: Descripción de qué se consultó
        
        Returns:
            str: Respuesta en lenguaje natural
        """
        
        prompt = f"""
Convierte estos datos de reporte en una respuesta natural y amigable en español.

REPORTE SOLICITADO:
{descripcion_reporte}

DATOS DEL REPORTE:
{json.dumps(datos_reporte, indent=2, default=str)}

INSTRUCCIONES:
1. Sé conciso pero informativo
2. Usa formato legible (bullets, números)
3. Destaca los datos más importantes
4. Usa emojis relevantes para hacer más visual
5. Si hay alertas o datos preocupantes, menciónalos
6. Termina con un insight o recomendación breve si es relevante

EJEMPLO:

Para ventas del mes:
"📊 Ventas de Enero 2024

💰 Ingresos totales: $45,000
🛒 Número de ventas: 120
💳 Ticket promedio: $375

Desglose por tipo de pago:
• Contado: 80 ventas ($30,000)
• Crédito: 40 ventas ($15,000)

✅ Excelente mes! Superaste el objetivo en un 12%"

RESPONDE SOLO CON EL TEXTO, SIN COMILLAS NI FORMATO JSON.
"""
        
        try:
            response = openai.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": "Eres un analista de negocios que explica reportes de forma clara y amigable."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Fallback: devolver datos en formato simple
            return f"Resultado del reporte:\n{json.dumps(datos_reporte, indent=2, default=str)}"


class InterpretadorFechas:
    """Utilidad para interpretar expresiones de tiempo en español"""
    
    @staticmethod
    def interpretar(expresion):
        """
        Interpreta expresiones como "este mes", "la semana pasada", etc.
        
        Args:
            expresion: str como "este mes", "ayer", "último trimestre"
        
        Returns:
            tuple: (fecha_inicio, fecha_fin)
        """
        hoy = timezone.now().date()
        expresion = expresion.lower()
        
        # Hoy
        if 'hoy' in expresion:
            return hoy, hoy
        
        # Ayer
        if 'ayer' in expresion:
            ayer = hoy - timedelta(days=1)
            return ayer, ayer
        
        # Esta semana
        if 'esta semana' in expresion or 'semana actual' in expresion:
            inicio = hoy - timedelta(days=hoy.weekday())
            return inicio, hoy
        
        # Semana pasada
        if 'semana pasada' in expresion or 'última semana' in expresion:
            fin = hoy - timedelta(days=hoy.weekday() + 1)
            inicio = fin - timedelta(days=6)
            return inicio, fin
        
        # Este mes
        if 'este mes' in expresion or 'mes actual' in expresion:
            inicio = hoy.replace(day=1)
            return inicio, hoy
        
        # Mes pasado
        if 'mes pasado' in expresion or 'último mes' in expresion:
            primer_dia_mes_actual = hoy.replace(day=1)
            fin = primer_dia_mes_actual - timedelta(days=1)
            inicio = fin.replace(day=1)
            return inicio, fin
        
        # Este año
        if 'este año' in expresion or 'año actual' in expresion:
            inicio = hoy.replace(month=1, day=1)
            return inicio, hoy
        
        # Último trimestre
        if 'trimestre' in expresion or 'últimos 3 meses' in expresion:
            inicio = hoy - timedelta(days=90)
            return inicio, hoy
        
        # Por defecto: último mes
        return hoy - timedelta(days=30), hoy