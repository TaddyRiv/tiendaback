from django.utils import timezone
from datetime import timedelta
from productos.models import Product, ProviderProduct
from .predictor_demanda import PredictorDemanda
from .analizador_historico import AnalizadorHistorico


class RecomendadorCompras:
    """Sistema que decide qué, cuánto y cuándo comprar"""
    
    # Configuración de negocio
    CONFIG = {
        'dias_stock_seguridad': 15,  # Buffer de seguridad
        'dias_lead_time': 7,  # Tiempo de entrega del proveedor
        'presupuesto_maximo': 100000,  # Presupuesto disponible
        'margen_minimo_urgencia': 0.8,  # 80% del punto de reorden = urgente
    }
    
    @classmethod
    def recomendar_producto(cls, producto_id, dias_proyeccion=60):
        """
        Genera recomendación de compra para un producto
        
        Returns:
            dict con recomendación completa
        """
        producto = Product.objects.get(id=producto_id)
        
        # Obtener predicción
        prediccion = PredictorDemanda.predecir(producto_id, dias_proyeccion)
        
        # usar .get para evitar KeyError si la predicción tiene otra estructura
        if prediccion.get('confianza', 0) == 0:
            return cls._recomendacion_sin_datos(producto)
        
        # Análisis histórico
        analisis = AnalizadorHistorico.analizar_producto(producto_id)
        
        # Calcular necesidades
        demanda_predicha = prediccion.get('prediccion', prediccion.get('prediccion_unidades', 0))
        demanda_diaria = prediccion.get('prediccion_diaria', round(prediccion.get('prediccion_unidades', 0) / 30, 2))
        stock_actual = producto.stock
        
        # Stock de seguridad
        stock_seguridad = demanda_diaria * cls.CONFIG['dias_stock_seguridad']
        
        # Punto de reorden
        dias_totales = dias_proyeccion + cls.CONFIG['dias_lead_time'] + cls.CONFIG['dias_stock_seguridad']
        punto_reorden = demanda_diaria * dias_totales
        
        # Decisión de compra
        necesita_compra = stock_actual < punto_reorden
        
        if necesita_compra:
            return cls._generar_recomendacion_compra(
                producto, prediccion, analisis, demanda_diaria, 
                stock_actual, punto_reorden, stock_seguridad
            )
        else:
            return cls._generar_recomendacion_no_comprar(
                producto, prediccion, stock_actual, demanda_diaria
            )
    
    @classmethod
    def _generar_recomendacion_compra(cls, producto, prediccion, analisis, 
                                      demanda_diaria, stock_actual, punto_reorden, stock_seguridad):
        """Genera recomendación de COMPRA"""
        
        # Cantidad a comprar
        cantidad_base = punto_reorden - stock_actual
        
        # Ajustar por temporada
        factor_temporal = cls._calcular_factor_ajuste_temporal(analisis)
        cantidad_ajustada = cantidad_base * factor_temporal
        
        # Redondear a múltiplos razonables
        cantidad_final = cls._redondear_cantidad(cantidad_ajustada)
        
        # Calcular urgencia
        urgencia = cls._calcular_urgencia(stock_actual, demanda_diaria, punto_reorden)
        
        # Calcular fechas
        dias_cobertura = stock_actual / demanda_diaria if demanda_diaria > 0 else 999
        fecha_agotamiento = timezone.now().date() + timedelta(days=int(dias_cobertura))
        fecha_compra_sugerida = fecha_agotamiento - timedelta(days=cls.CONFIG['dias_lead_time'] + cls.CONFIG['dias_stock_seguridad'])
        
        # Calcular costos (si hay precio de compra)
        try:
            proveedor_producto = ProviderProduct.objects.filter(producto=producto).first()
            precio_compra = float(proveedor_producto.precio_compra) if proveedor_producto and proveedor_producto.precio_compra else float(producto.precio) * 0.6
        except:
            precio_compra = float(producto.precio) * 0.6  # Estimado 60% del precio venta
        
        costo_total = cantidad_final * precio_compra
        ganancia_estimada = cantidad_final * (float(producto.precio) - precio_compra)
        roi = ganancia_estimada / costo_total if costo_total > 0 else 0
        
        # Construir recomendación
        recomendacion = {
            'producto_id': producto.id,
            'nombre': producto.nombre,
            'categoria': producto.categoria.descripcion,
            
            'accion': 'COMPRAR',
            'urgencia': urgencia['nivel'],
            'prioridad': urgencia['prioridad'],
            
            'cantidad_recomendada': cantidad_final,
            'razon': cls._generar_razon_compra(urgencia, analisis, prediccion),
            
            'stock': {
                'actual': stock_actual,
                'punto_reorden': round(punto_reorden),
                'stock_seguridad': round(stock_seguridad),
                'dias_cobertura': round(dias_cobertura, 1),
                'fecha_agotamiento_estimada': fecha_agotamiento.isoformat()
            },
            
            'prediccion': {
                'demanda_60_dias': prediccion.get('prediccion', prediccion.get('prediccion_unidades', 0)),
                'demanda_diaria': demanda_diaria,
                'confianza': prediccion.get('confianza', 0),
                'metodo': prediccion.get('metodo')
            },
            
            'financiero': {
                'precio_compra_unitario': round(precio_compra, 2),
                'costo_total': round(costo_total, 2),
                'precio_venta_unitario': float(producto.precio),
                'ganancia_estimada': round(ganancia_estimada, 2),
                'roi': round(roi, 2)
            },
            
            'fechas': {
                'comprar_antes_de': fecha_compra_sugerida.isoformat(),
                'dias_para_comprar': (fecha_compra_sugerida - timezone.now().date()).days
            },
            
            'factores_considerados': {
                'factor_temporal': round(factor_temporal, 2),
                'temporada_actual': AnalizadorHistorico.obtener_temporada_actual(),
                'tendencia': analisis['tendencia'],
                'velocidad_rotacion': analisis['velocidad']
            }
        }
        
        # Agregar alertas si es urgente
        if urgencia['nivel'] in ['CRÍTICO', 'ALTO']:
            recomendacion['alertas'] = urgencia['alertas']
        
        return recomendacion
    
    @classmethod
    def _generar_recomendacion_no_comprar(cls, producto, prediccion, stock_actual, demanda_diaria):
        """Genera recomendación de NO COMPRAR"""
        dias_cobertura = stock_actual / demanda_diaria if demanda_diaria > 0 else 999
        
        return {
            'producto_id': producto.id,
            'nombre': producto.nombre,
            'categoria': producto.categoria.descripcion,
            
            'accion': 'NO_COMPRAR',
            'urgencia': 'BAJA',
            'razon': f'Stock suficiente para {round(dias_cobertura)} días',
            
            'stock': {
                'actual': stock_actual,
                'dias_cobertura': round(dias_cobertura, 1)
            },
            
            'prediccion': {
                'demanda_60_dias': prediccion.get('prediccion', prediccion.get('prediccion_unidades', 0)),
                'demanda_diaria': demanda_diaria
            },
            
            'proxima_revision': (timezone.now().date() + timedelta(days=max(15, int(dias_cobertura/2)))).isoformat()
        }
    
    @classmethod
    def _recomendacion_sin_datos(cls, producto):
        """Recomendación para productos sin historial"""
        return {
            'producto_id': producto.id,
            'nombre': producto.nombre,
            'categoria': producto.categoria.descripcion,
            
            'accion': 'SIN_DATOS',
            'razon': 'Producto sin historial de ventas',
            'recomendacion': 'Comprar cantidad inicial conservadora (10-20 unidades) o usar datos de productos similares',
            
            'stock_actual': producto.stock
        }
    
    @classmethod
    def _calcular_urgencia(cls, stock_actual, demanda_diaria, punto_reorden):
        """Calcula nivel de urgencia"""
        if demanda_diaria == 0:
            return {
                'nivel': 'BAJA',
                'prioridad': 10,
                'alertas': []
            }
        
        dias_cobertura = stock_actual / demanda_diaria
        porcentaje_punto_reorden = stock_actual / punto_reorden if punto_reorden > 0 else 1
        
        if dias_cobertura < 7 or porcentaje_punto_reorden < 0.3:
            return {
                'nivel': 'CRÍTICO',
                'prioridad': 1,
                'alertas': [
                    '🔴 STOCK CRÍTICO: Se agota en menos de 1 semana',
                    '⚡ COMPRAR INMEDIATAMENTE'
                ]
            }
        elif dias_cobertura < 15 or porcentaje_punto_reorden < 0.5:
            return {
                'nivel': 'ALTO',
                'prioridad': 2,
                'alertas': [
                    '🟠 Stock bajo: Se agota en 2 semanas',
                    '📦 Programar compra esta semana'
                ]
            }
        elif dias_cobertura < 30 or porcentaje_punto_reorden < 0.8:
            return {
                'nivel': 'MEDIO',
                'prioridad': 3,
                'alertas': [
                    '🟡 Stock moderado: Se agota en 1 mes'
                ]
            }
        else:
            return {
                'nivel': 'BAJA',
                'prioridad': 4,
                'alertas': []
            }
    
    @classmethod
    def _calcular_factor_ajuste_temporal(cls, analisis):
        """Ajusta cantidad según temporada próxima"""
        mes_actual = timezone.now().month
        mes_proximo = (mes_actual % 12) + 1
        
        # Si el próximo mes es temporada alta, comprar más
        if mes_proximo in analisis['temporada_alta']:
            return 1.3
        elif mes_proximo in analisis['temporada_baja']:
            return 0.7
        else:
            return 1.0
    
    @classmethod
    def _redondear_cantidad(cls, cantidad):
        """Redondea a múltiplos razonables"""
        if cantidad < 10:
            return max(5, round(cantidad))
        elif cantidad < 50:
            return round(cantidad / 5) * 5  # Múltiplos de 5
        elif cantidad < 200:
            return round(cantidad / 10) * 10  # Múltiplos de 10
        else:
            return round(cantidad / 25) * 25  # Múltiplos de 25
    
    @classmethod
    def _generar_razon_compra(cls, urgencia, analisis, prediccion):
        """Genera razón humanizada de por qué comprar"""
        razones = []
        
        if urgencia['nivel'] == 'CRÍTICO':
            razones.append('Stock crítico')
        elif urgencia['nivel'] == 'ALTO':
            razones.append('Stock bajo')
        
        if analisis['tendencia'] == 'creciente':
            razones.append(f"Ventas creciendo {abs(analisis['crecimiento_mensual'])}%")
        
        temporada = AnalizadorHistorico.obtener_temporada_actual()
        razones.append(f"Temporada: {temporada}")
        
        return ' | '.join(razones)
    
    @classmethod
    def recomendar_categoria(cls, categoria_id, limite=None):
        """Genera recomendaciones para toda una categoría"""
        productos = Product.objects.filter(categoria_id=categoria_id)
        
        if limite:
            productos = productos[:limite]
        
        recomendaciones = []
        for producto in productos:
            try:
                rec = cls.recomendar_producto(producto.id)
                recomendaciones.append(rec)
            except Exception as e:
                print(f"Error en producto {producto.id}: {e}")
                continue
        
        # Ordenar por prioridad
        recomendaciones.sort(key=lambda x: x.get('prioridad', 999))
        
        return recomendaciones
    
    @classmethod
    def recomendar_todos(cls, solo_necesarios=True):
        """Genera recomendaciones para todos los productos"""
        productos = Product.objects.all()
        
        recomendaciones = []
        estadisticas = {
            'total_productos': 0,
            'comprar': 0,
            'no_comprar': 0,
            'criticos': 0,
            'sin_datos': 0,
            'inversion_total': 0
        }
        
        for producto in productos:
            try:
                rec = cls.recomendar_producto(producto.id)
                
                estadisticas['total_productos'] += 1
                
                if rec['accion'] == 'COMPRAR':
                    if not solo_necesarios or rec['urgencia'] != 'BAJA':
                        recomendaciones.append(rec)
                        estadisticas['comprar'] += 1
                        estadisticas['inversion_total'] += rec['financiero']['costo_total']
                        
                        if rec['urgencia'] == 'CRÍTICO':
                            estadisticas['criticos'] += 1
                elif rec['accion'] == 'NO_COMPRAR':
                    estadisticas['no_comprar'] += 1
                else:
                    estadisticas['sin_datos'] += 1
                    
            except Exception as e:
                print(f"Error en producto {producto.id}: {e}")
                continue
        
        # Ordenar por prioridad
        recomendaciones.sort(key=lambda x: x.get('prioridad', 999))
        
        return {
            'recomendaciones': recomendaciones,
            'estadisticas': estadisticas,
            'fecha_analisis': timezone.now().isoformat()
        }