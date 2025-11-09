"""
PREDICTOR DE DEMANDA CON MACHINE LEARNING
Coloca este archivo en: reportes/ml_models/predictor_demanda.py
"""

import numpy as np
from datetime import timedelta
from django.utils import timezone
from .analizador_historico import AnalizadorHistorico


class PredictorDemanda:
    """Sistema híbrido de predicción de demanda"""
    
    @classmethod
    def predecir(cls, producto_id, dias_futuro=30):
        """
        Predice demanda futura usando enfoque híbrido
        
        Args:
            producto_id: ID del producto
            dias_futuro: Días a predecir (default 30)
        
        Returns:
            dict con predicción y confianza
        """
        # Obtener análisis histórico
                # 🔹 Intentar usar modelo entrenado de ML (si existe)
        try:
            from .predictor_ml import predecir_demanda_rf
            resultado_ml = predecir_demanda_rf(producto_id, dias_futuro)
            resultado_ml["confianza"] = 0.9
            resultado_ml["metodo"] = "RandomForest"
            resultado_ml["comentario"] = "Predicción generada con modelo ML entrenado"
            return resultado_ml
        except Exception as e:
            print(f"⚠️ ML no disponible ({e}), usando método estadístico tradicional...")

        analisis = AnalizadorHistorico.analizar_producto(producto_id)
        
        if analisis.get('sin_historial'):
            return cls._prediccion_sin_datos(analisis, dias_futuro)
        
        # Determinar método según datos disponibles
        meses_datos = analisis['meses_con_datos']
        
        if meses_datos < 3:
            # Pocos datos: usar último mes + ajuste temporal
            return cls._prediccion_ultimo_mes(analisis, dias_futuro)
        elif meses_datos < 6:
            # Datos moderados: promedio móvil ponderado
            return cls._prediccion_promedio_movil(analisis, dias_futuro)
        elif meses_datos < 12:
            # Buenos datos: promedio + tendencia
            return cls._prediccion_con_tendencia(analisis, dias_futuro)
        else:
            # Muchos datos: híbrido completo con estacionalidad
            return cls._prediccion_hibrida_completa(analisis, dias_futuro)
    
    @classmethod
    def _prediccion_ultimo_mes(cls, analisis, dias):
        """Predicción basada solo en último mes"""
        ventas_ultimo_mes = analisis['ventas_ultimo_mes']
        
        # Extrapolación lineal
        ventas_diarias = ventas_ultimo_mes / 30
        prediccion_base = ventas_diarias * dias
        
        # Ajuste por temporada
        factor_temporal = cls._calcular_factor_temporal(analisis, dias)
        prediccion_ajustada = prediccion_base * factor_temporal
        
        # Intervalo de confianza (±30% por poca data)
        intervalo = prediccion_ajustada * 0.3
        
        return {
            'prediccion': round(prediccion_ajustada),
            'prediccion_diaria': round(ventas_diarias * factor_temporal, 2),
            'confianza': 0.60,
            'metodo': 'ultimo_mes',
            'intervalo_min': round(prediccion_ajustada - intervalo),
            'intervalo_max': round(prediccion_ajustada + intervalo),
            'factores': {
                'ventas_ultimo_mes': ventas_ultimo_mes,
                'factor_temporal': round(factor_temporal, 2),
                'dias_proyectados': dias
            },
            'advertencia': 'Predicción con datos limitados (<3 meses)'
        }
    
    @classmethod
    def _prediccion_promedio_movil(cls, analisis, dias):
        """Promedio móvil ponderado de últimos meses"""
        # Simular últimos 3 meses (si tuviéramos el detalle)
        # Por ahora usamos promedio mensual
        promedio_mensual = analisis['ventas_promedio_mensual']
        ventas_diarias = promedio_mensual / 30
        
        prediccion_base = ventas_diarias * dias
        
        # Ajustar por tendencia
        if analisis['tendencia'] == 'creciente':
            factor_tendencia = 1 + (analisis['crecimiento_mensual'] / 100)
        elif analisis['tendencia'] == 'decreciente':
            factor_tendencia = 1 + (analisis['crecimiento_mensual'] / 100)
        else:
            factor_tendencia = 1.0
        
        # Ajustar por temporada
        factor_temporal = cls._calcular_factor_temporal(analisis, dias)
        
        prediccion_final = prediccion_base * factor_tendencia * factor_temporal
        
        # Intervalo de confianza (±20%)
        intervalo = prediccion_final * 0.2
        
        return {
            'prediccion': round(prediccion_final),
            'prediccion_diaria': round((ventas_diarias * factor_tendencia * factor_temporal), 2),
            'confianza': 0.75,
            'metodo': 'promedio_movil',
            'intervalo_min': round(prediccion_final - intervalo),
            'intervalo_max': round(prediccion_final + intervalo),
            'factores': {
                'promedio_mensual': promedio_mensual,
                'factor_tendencia': round(factor_tendencia, 2),
                'factor_temporal': round(factor_temporal, 2)
            }
        }
    
    @classmethod
    def _prediccion_con_tendencia(cls, analisis, dias):
        """Predicción con análisis de tendencia"""
        promedio_mensual = analisis['ventas_promedio_mensual']
        ventas_diarias = promedio_mensual / 30
        
        # Aplicar tendencia
        crecimiento = analisis['crecimiento_mensual'] / 100
        meses_proyeccion = dias / 30
        factor_tendencia = (1 + crecimiento) ** meses_proyeccion
        
        prediccion_con_tendencia = ventas_diarias * dias * factor_tendencia
        
        # Ajustar por temporada
        factor_temporal = cls._calcular_factor_temporal(analisis, dias)
        
        prediccion_final = prediccion_con_tendencia * factor_temporal
        
        # Intervalo de confianza (±15%)
        intervalo = prediccion_final * 0.15
        
        return {
            'prediccion': round(prediccion_final),
            'prediccion_diaria': round((ventas_diarias * factor_tendencia * factor_temporal), 2),
            'confianza': 0.82,
            'metodo': 'con_tendencia',
            'intervalo_min': round(prediccion_final - intervalo),
            'intervalo_max': round(prediccion_final + intervalo),
            'factores': {
                'tendencia': analisis['tendencia'],
                'crecimiento_mensual': analisis['crecimiento_mensual'],
                'factor_tendencia': round(factor_tendencia, 2),
                'factor_temporal': round(factor_temporal, 2)
            }
        }
    
    @classmethod
    def _prediccion_hibrida_completa(cls, analisis, dias):
        """Predicción híbrida completa con todos los factores"""
        # Base: promedio ajustado por estacionalidad histórica
        mes_target = (timezone.now() + timedelta(days=dias)).month
        
        ventas_mes_historico = analisis['ventas_por_mes'].get(mes_target, {})
        promedio_mes_target = ventas_mes_historico.get('promedio', analisis['ventas_promedio_mensual'])
        
        # Si no hay datos del mes target, usar promedio general
        if promedio_mes_target == 0:
            promedio_mes_target = analisis['ventas_promedio_mensual']
        
        ventas_diarias = promedio_mes_target / 30
        
        # Factor de tendencia
        crecimiento = analisis['crecimiento_mensual'] / 100
        meses_proyeccion = dias / 30
        factor_tendencia = (1 + crecimiento) ** meses_proyeccion
        
        # Factor temporal (estacionalidad futura)
        factor_temporal = cls._calcular_factor_temporal(analisis, dias)
        
        # Combinar factores
        prediccion_final = ventas_diarias * dias * factor_tendencia * factor_temporal
        
        # Intervalo de confianza (±10% con mucha data)
        intervalo = prediccion_final * 0.10
        
        return {
            'prediccion': round(prediccion_final),
            'prediccion_diaria': round((ventas_diarias * factor_tendencia * factor_temporal), 2),
            'confianza': 0.88,
            'metodo': 'hibrido_completo',
            'intervalo_min': round(prediccion_final - intervalo),
            'intervalo_max': round(prediccion_final + intervalo),
            'factores': {
                'promedio_mes_target': round(promedio_mes_target, 2),
                'tendencia': analisis['tendencia'],
                'crecimiento_mensual': analisis['crecimiento_mensual'],
                'factor_tendencia': round(factor_tendencia, 2),
                'factor_temporal': round(factor_temporal, 2),
                'mes_objetivo': mes_target
            },
            'estacionalidad': {
                'temporada_alta': analisis['temporada_alta'],
                'temporada_baja': analisis['temporada_baja'],
                'mes_mas_fuerte': analisis['mes_mas_fuerte']
            }
        }
    
    @classmethod
    def _prediccion_sin_datos(cls, analisis, dias):
        """Predicción para productos sin historial"""
        return {
            'prediccion': 0,
            'prediccion_diaria': 0,
            'confianza': 0.0,
            'metodo': 'sin_datos',
            'advertencia': 'Producto sin historial de ventas',
            'recomendacion': f'Usar datos de productos similares en categoría: {analisis["categoria"]}'
        }
    
    @classmethod
    def _calcular_factor_temporal(cls, analisis, dias_futuro):
        """
        Calcula factor de ajuste temporal según:
        - Temporada actual vs temporada futura
        - Proximidad a fechas especiales
        - Patrones históricos del producto
        """
        fecha_futura = timezone.now().date() + timedelta(days=dias_futuro)
        mes_futuro = fecha_futura.month
        
        # Factor base = 1.0 (sin ajuste)
        factor = 1.0
        
        # Ajuste por estacionalidad histórica del producto
        if mes_futuro in analisis['temporada_alta']:
            # Mes históricamente fuerte
            factor *= 1.3
        elif mes_futuro in analisis['temporada_baja']:
            # Mes históricamente débil
            factor *= 0.7
        
        # Ajuste por eventos próximos
        eventos = AnalizadorHistorico.calcular_proximidad_eventos(fecha_futura)
        
        for evento in eventos:
            if evento['dias_hasta'] <= 30:
                # Hay un evento cercano, aumentar factor
                if evento['evento'] == 'navidad':
                    factor *= 1.4
                elif evento['evento'] in ['dia_madre', 'dia_padre', 'san_valentin']:
                    factor *= 1.2
                else:
                    factor *= 1.1
        
        # Limitar factor entre 0.5 y 2.0 (no menos de 50%, no más del doble)
        factor = max(0.5, min(2.0, factor))
        
        return factor
    
    @classmethod
    def predecir_multiples_periodos(cls, producto_id):
        """Predice para 30, 60 y 90 días"""
        return {
            '30_dias': cls.predecir(producto_id, 30),
            '60_dias': cls.predecir(producto_id, 60),
            '90_dias': cls.predecir(producto_id, 90)
        }