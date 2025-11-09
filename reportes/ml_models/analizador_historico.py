from django.db.models import Sum, Count, Avg, Max, Min
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from datetime import timedelta, date
from collections import defaultdict
import numpy as np

from ventas.models import SalesNote, DetailNote
from productos.models import Product


class AnalizadorHistorico:
    """Analiza patrones históricos de ventas"""
    
    # Configuración para Bolivia (Hemisferio Sur)
    TEMPORADAS = {
        "verano": [12, 1, 2],      # Diciembre, Enero, Febrero
        "otoño": [3, 4, 5],        # Marzo, Abril, Mayo
        "invierno": [6, 7, 8],     # Junio, Julio, Agosto
        "primavera": [9, 10, 11]   # Septiembre, Octubre, Noviembre
    }
    
    FECHAS_ESPECIALES = {
        "navidad": {"mes": 12, "dia": 25, "anticipacion_dias": 45},
        "año_nuevo": {"mes": 1, "dia": 1, "anticipacion_dias": 30},
        "san_valentin": {"mes": 2, "dia": 14, "anticipacion_dias": 30},
        "carnaval": {"mes": 2, "dia_variable": True, "anticipacion_dias": 20},
        "dia_madre": {"mes": 5, "dia_variable": True, "anticipacion_dias": 30},
        "dia_padre": {"mes": 6, "dia_variable": True, "anticipacion_dias": 30},
        "todos_santos": {"mes": 11, "dia": 2, "anticipacion_dias": 15}
    }
    
    @classmethod
    def analizar_producto(cls, producto_id, meses_historico=12):
        """
        Analiza un producto específico
        
        Returns:
            dict con análisis completo del producto
        """
        producto = Product.objects.get(id=producto_id)
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=meses_historico * 30)
        
        # Obtener ventas históricas
        ventas_mensuales = DetailNote.objects.filter(
            producto=producto,
            nota__fecha__gte=fecha_inicio,
            nota__fecha__lte=fecha_fin
        ).annotate(
            mes=TruncMonth('nota__fecha')
        ).values('mes').annotate(
            cantidad=Sum('cantidad'),
            ingresos=Sum('subtotal')
        ).order_by('mes')
        
        ventas_mensuales_list = list(ventas_mensuales)
        
        if not ventas_mensuales_list:
            return cls._analisis_sin_datos(producto)
        
        # Análisis básico
        total_ventas = sum(v['cantidad'] for v in ventas_mensuales_list)
        promedio_mensual = total_ventas / len(ventas_mensuales_list)
        
        # Ventas por mes del año
        ventas_por_mes_año = cls._agrupar_por_mes_año(ventas_mensuales_list)
        
        # Detectar estacionalidad
        estacionalidad = cls._detectar_estacionalidad(ventas_por_mes_año)
        
        # Calcular tendencia
        tendencia = cls._calcular_tendencia(ventas_mensuales_list)
        
        # Velocidad de rotación
        rotacion = cls._calcular_rotacion(producto, ventas_mensuales_list)
        
        # Último mes
        ultimo_mes = ventas_mensuales_list[-1] if ventas_mensuales_list else None
        
        return {
            'producto_id': producto.id,
            'nombre': producto.nombre,
            'categoria': producto.categoria.descripcion,
            'precio': float(producto.precio),
            'stock_actual': producto.stock,
            
            # Ventas históricas
            'ventas_totales': total_ventas,
            'ventas_promedio_mensual': round(promedio_mensual, 2),
            'meses_con_datos': len(ventas_mensuales_list),
            
            # Último mes
            'ventas_ultimo_mes': ultimo_mes['cantidad'] if ultimo_mes else 0,
            'ingresos_ultimo_mes': float(ultimo_mes['ingresos']) if ultimo_mes else 0,
            
            # Estacionalidad
            'ventas_por_mes': ventas_por_mes_año,
            'temporada_alta': estacionalidad['temporada_alta'],
            'temporada_baja': estacionalidad['temporada_baja'],
            'factor_estacional_max': estacionalidad['factor_max'],
            'mes_mas_fuerte': estacionalidad['mes_mas_fuerte'],
            
            # Tendencia
            'tendencia': tendencia['direccion'],
            'crecimiento_mensual': tendencia['crecimiento_pct'],
            'es_estable': tendencia['es_estable'],
            
            # Rotación
            'dias_promedio_agotamiento': rotacion['dias_agotamiento'],
            'rotacion_diaria': rotacion['rotacion_diaria'],
            'velocidad': rotacion['clasificacion']
        }
    
    @classmethod
    def _agrupar_por_mes_año(cls, ventas_mensuales):
        """Agrupa ventas por mes del año (ej: todos los eneros juntos)"""
        ventas_mes = defaultdict(list)
        
        for venta in ventas_mensuales:
            mes_num = venta['mes'].month
            ventas_mes[mes_num].append(venta['cantidad'])
        
        resultado = {}
        for mes in range(1, 13):
            if mes in ventas_mes:
                resultado[mes] = {
                    'promedio': np.mean(ventas_mes[mes]),
                    'total': sum(ventas_mes[mes]),
                    'veces': len(ventas_mes[mes])
                }
            else:
                resultado[mes] = {'promedio': 0, 'total': 0, 'veces': 0}
        
        return resultado
    
    @classmethod
    def _detectar_estacionalidad(cls, ventas_por_mes):
        """Detecta temporadas altas y bajas"""
        promedios = {mes: data['promedio'] for mes, data in ventas_por_mes.items()}
        
        if not any(promedios.values()):
            return {
                'temporada_alta': [],
                'temporada_baja': [],
                'factor_max': 1.0,
                'mes_mas_fuerte': None
            }
        
        promedio_general = np.mean([v for v in promedios.values() if v > 0])
        
        # Meses con ventas >120% del promedio = alta temporada
        # Meses con ventas <80% del promedio = baja temporada
        temporada_alta = [mes for mes, prom in promedios.items() 
                          if prom > promedio_general * 1.2]
        temporada_baja = [mes for mes, prom in promedios.items() 
                          if 0 < prom < promedio_general * 0.8]
        
        mes_mas_fuerte = max(promedios, key=promedios.get) if promedios else None
        factor_max = promedios[mes_mas_fuerte] / promedio_general if mes_mas_fuerte and promedio_general > 0 else 1.0
        
        return {
            'temporada_alta': temporada_alta,
            'temporada_baja': temporada_baja,
            'factor_max': round(factor_max, 2),
            'mes_mas_fuerte': mes_mas_fuerte
        }
    
    @classmethod
    def _calcular_tendencia(cls, ventas_mensuales):
        """Calcula tendencia de crecimiento"""
        if len(ventas_mensuales) < 2:
            return {
                'direccion': 'sin_datos',
                'crecimiento_pct': 0,
                'es_estable': True
            }
        
        cantidades = [v['cantidad'] for v in ventas_mensuales]
        
        # Regresión lineal simple
        x = np.arange(len(cantidades))
        y = np.array(cantidades)
        
        if len(x) > 1 and np.std(y) > 0:
            # Pendiente de la línea de tendencia
            coef = np.polyfit(x, y, 1)[0]
            
            # Crecimiento porcentual mensual
            promedio = np.mean(y)
            crecimiento_pct = (coef / promedio * 100) if promedio > 0 else 0
            
            # Determinar dirección
            if crecimiento_pct > 5:
                direccion = 'creciente'
            elif crecimiento_pct < -5:
                direccion = 'decreciente'
            else:
                direccion = 'estable'
            
            # Estabilidad (variación)
            cv = (np.std(y) / np.mean(y)) if np.mean(y) > 0 else 0
            es_estable = cv < 0.3  # Coeficiente de variación <30%
            
            return {
                'direccion': direccion,
                'crecimiento_pct': round(crecimiento_pct, 2),
                'es_estable': es_estable
            }
        
        return {
            'direccion': 'estable',
            'crecimiento_pct': 0,
            'es_estable': True
        }
    
    @classmethod
    def _calcular_rotacion(cls, producto, ventas_mensuales):
        """Calcula velocidad de rotación del producto"""
        if not ventas_mensuales:
            return {
                'dias_agotamiento': 999,
                'rotacion_diaria': 0,
                'clasificacion': 'sin_movimiento'
            }
        
        # Ventas promedio diarias (últimos 3 meses)
        ultimos_90_dias = ventas_mensuales[-3:] if len(ventas_mensuales) >= 3 else ventas_mensuales
        total_dias = len(ultimos_90_dias) * 30
        total_vendido = sum(v['cantidad'] for v in ultimos_90_dias)
        
        rotacion_diaria = total_vendido / total_dias if total_dias > 0 else 0
        
        # Días hasta agotamiento
        if rotacion_diaria > 0:
            dias_agotamiento = producto.stock / rotacion_diaria
        else:
            dias_agotamiento = 999
        
        # Clasificación
        if rotacion_diaria >= 5:
            clasificacion = 'muy_rapida'
        elif rotacion_diaria >= 2:
            clasificacion = 'rapida'
        elif rotacion_diaria >= 0.5:
            clasificacion = 'normal'
        elif rotacion_diaria > 0:
            clasificacion = 'lenta'
        else:
            clasificacion = 'sin_movimiento'
        
        return {
            'dias_agotamiento': round(dias_agotamiento, 1),
            'rotacion_diaria': round(rotacion_diaria, 2),
            'clasificacion': clasificacion
        }
    
    @classmethod
    def _analisis_sin_datos(cls, producto):
        """Análisis para productos sin historial"""
        return {
            'producto_id': producto.id,
            'nombre': producto.nombre,
            'categoria': producto.categoria.descripcion,
            'precio': float(producto.precio),
            'stock_actual': producto.stock,
            'ventas_totales': 0,
            'ventas_promedio_mensual': 0,
            'meses_con_datos': 0,
            'sin_historial': True,
            'recomendacion': 'Usar datos de productos similares de la misma categoría'
        }
    
    @classmethod
    def obtener_temporada_actual(cls):
        """Obtiene la temporada actual"""
        mes_actual = timezone.now().month
        
        for temporada, meses in cls.TEMPORADAS.items():
            if mes_actual in meses:
                return temporada
        
        return 'desconocida'
    
    @classmethod
    def calcular_proximidad_eventos(cls, fecha_referencia=None):
        """Calcula días hasta fechas especiales"""
        if fecha_referencia is None:
            fecha_referencia = timezone.now().date()
        
        eventos_proximos = []
        
        for evento, config in cls.FECHAS_ESPECIALES.items():
            if config.get('dia_variable'):
                continue  # Requiere cálculo especial
            
            # Crear fecha del evento este año
            try:
                fecha_evento = date(fecha_referencia.year, config['mes'], config['dia'])
            except ValueError:
                continue
            
            # Si ya pasó, usar el próximo año
            if fecha_evento < fecha_referencia:
                try:
                    fecha_evento = date(fecha_referencia.year + 1, config['mes'], config['dia'])
                except ValueError:
                    continue
            
            dias_hasta = (fecha_evento - fecha_referencia).days
            
            if dias_hasta <= config['anticipacion_dias']:
                eventos_proximos.append({
                    'evento': evento,
                    'fecha': fecha_evento,
                    'dias_hasta': dias_hasta,
                    'anticipacion_dias': config['anticipacion_dias'],
                    'es_momento_comprar': dias_hasta >= 15  # Comprar con al menos 15 días
                })
        
        return sorted(eventos_proximos, key=lambda x: x['dias_hasta'])
    
    @classmethod
    def analizar_categoria(cls, categoria_id, meses_historico=12):
        """Analiza todos los productos de una categoría"""
        productos = Product.objects.filter(categoria_id=categoria_id)
        
        analisis = []
        for producto in productos:
            try:
                analisis.append(cls.analizar_producto(producto.id, meses_historico))
            except Exception as e:
                print(f"Error analizando producto {producto.id}: {e}")
                continue
        
        return analisis