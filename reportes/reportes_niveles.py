from django.db.models import (
    Sum, Count, Avg, Max, Min, F, Q, ExpressionWrapper,
    DecimalField, FloatField, Case, When, Value, IntegerField
)
from django.db import models
from django.db.models.functions import (
    TruncDate, TruncMonth, TruncWeek, Coalesce, ExtractMonth, ExtractYear
)
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from ventas.models import SalesNote, DetailNote, CashPayment
from creditos.models import CreditSale, CreditInstallment, CreditPayment, CreditConfig
from productos.models import Product, Category, Provider
from usuarios.models import Usuario



# reportes nivel 1


class ReportesBasicos:
    """Reportes simples y rápidos para uso diario"""
    
    @staticmethod
    def ventas_por_periodo(fecha_inicio, fecha_fin):
        """Resumen de ventas en un período"""
        ventas = SalesNote.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin]
        ).aggregate(
            total_ventas=Count('id'),
            ingresos_totales=Sum('monto'),
            ticket_promedio=Avg('monto'),
            venta_maxima=Max('monto'),
            venta_minima=Min('monto')
        )
        
        # Desglose por tipo de pago
        por_tipo_pago = SalesNote.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin]
        ).values('tipo_pago').annotate(
            cantidad=Count('id'),
            monto_total=Sum('monto')
        ).order_by('-monto_total')
        
        return {
            'resumen': ventas,
            'por_tipo_pago': list(por_tipo_pago),
            'periodo': {
                'inicio': fecha_inicio,
                'fin': fecha_fin
            }
        }
    
    @staticmethod
    def top_productos(fecha_inicio, fecha_fin, limite=10):
        """Productos más vendidos"""
        productos = DetailNote.objects.filter(
            nota__fecha__range=[fecha_inicio, fecha_fin]
        ).values(
            'producto__id',
            'producto__nombre',
            'producto__categoria__descripcion'
        ).annotate(
            unidades_vendidas=Sum('cantidad'),
            ingresos_generados=Sum('subtotal'),
            num_ventas=Count('nota', distinct=True)
        ).order_by('-unidades_vendidas')[:limite]
        
        return list(productos)
    
    @staticmethod
    def productos_bajo_stock(minimo=10):
        """Productos que necesitan reabastecimiento"""
        productos = Product.objects.filter(stock__lt=minimo).annotate(
            vendidos_30_dias=Coalesce(
                Sum('detailnote__cantidad',
                    filter=Q(detailnote__fecha__gte=timezone.now().date() - timedelta(days=30))),
                0
            )
        ).values(
            'id', 'nombre', 'stock', 'vendidos_30_dias',
            'categoria__descripcion', 'precio'
        ).order_by('stock')
        
        return list(productos)
    
    @staticmethod
    def ventas_por_dia(fecha_inicio, fecha_fin):
        """Ventas agrupadas por día"""
        ventas_diarias = SalesNote.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin]
        ).annotate(
            dia=TruncDate('fecha')
        ).values('dia').annotate(
            num_ventas=Count('id'),
            ingresos=Sum('monto')
        ).order_by('dia')
        
        return list(ventas_diarias)
    
    @staticmethod
    def resumen_creditos():
        """Estado actual de créditos"""
        return {
            'total_creditos_activos': CreditSale.objects.filter(estado='activo').count(),
            'monto_por_cobrar': CreditSale.objects.filter(
                estado='activo'
            ).aggregate(total=Sum('saldo_pendiente'))['total'] or 0,
            'creditos_atrasados': CreditSale.objects.filter(estado='atrasado').count(),
            'monto_atrasado': CreditSale.objects.filter(
                estado='atrasado'
            ).aggregate(total=Sum('saldo_pendiente'))['total'] or 0,
            'cuotas_vencidas_hoy': CreditInstallment.objects.filter(
                fecha_vencimiento__lte=timezone.now().date(),
                pagado=False
            ).count()
        }


# reportes nivele 2

class ReportesIntermedios:
    """Reportes con más análisis y cruces de datos"""
    
    @staticmethod
    def analisis_por_categoria(fecha_inicio, fecha_fin):
        """Rendimiento por categoría de producto"""
        categorias = Category.objects.annotate(
            num_productos=Count('productos'),
            ventas_periodo=Count(
                'productos__detailnote',
                filter=Q(productos__detailnote__fecha__range=[fecha_inicio, fecha_fin])
            ),
            unidades_vendidas=Sum(
                'productos__detailnote__cantidad',
                filter=Q(productos__detailnote__fecha__range=[fecha_inicio, fecha_fin])
            ),
            ingresos=Sum(
                'productos__detailnote__subtotal',
                filter=Q(productos__detailnote__fecha__range=[fecha_inicio, fecha_fin])
            ),
            precio_promedio=Avg('productos__precio')
        ).values(
            'id', 'descripcion', 'num_productos', 'ventas_periodo',
            'unidades_vendidas', 'ingresos', 'precio_promedio'
        ).order_by('-ingresos')
        
        return list(categorias)
    
    @staticmethod
    def rendimiento_empleados(fecha_inicio, fecha_fin):
        """Desempeño de empleados en ventas"""
        empleados = Usuario.objects.filter(
            ventas_realizadas__fecha__range=[fecha_inicio, fecha_fin]
        ).annotate(
            num_ventas=Count('ventas_realizadas'),
            monto_total_vendido=Sum('ventas_realizadas__monto'),
            ticket_promedio=Avg('ventas_realizadas__monto'),
            ventas_credito=Count(
                'ventas_realizadas',
                filter=Q(ventas_realizadas__tipo_pago='credito')
            ),
            ventas_contado=Count(
                'ventas_realizadas',
                filter=Q(ventas_realizadas__tipo_pago='contado')
            )
        ).values(
            'id', 'email', 'first_name', 'last_name',
            'num_ventas', 'monto_total_vendido', 'ticket_promedio',
            'ventas_credito', 'ventas_contado'
        ).order_by('-monto_total_vendido')
        
        return list(empleados)
    
    @staticmethod
    def analisis_clientes_frecuentes(limite=20):
        """Mejores clientes por compras y monto"""
        clientes = Usuario.objects.annotate(
            num_compras=Count('ventas_como_cliente'),
            monto_total=Sum('ventas_como_cliente__monto'),
            ticket_promedio=Avg('ventas_como_cliente__monto'),
            ultima_compra=Max('ventas_como_cliente__fecha'),
            tiene_creditos_activos=Count(
                'ventas_como_cliente__creditos',
                filter=Q(ventas_como_cliente__creditos__estado='activo')
            ),
            saldo_pendiente=Sum(
                'ventas_como_cliente__creditos__saldo_pendiente',
                filter=Q(ventas_como_cliente__creditos__estado='activo')
            )
        ).filter(
            num_compras__gt=0
        ).values(
            'id', 'email', 'first_name', 'last_name', 'telefono',
            'num_compras', 'monto_total', 'ticket_promedio',
            'ultima_compra', 'tiene_creditos_activos', 'saldo_pendiente',
            'estado_credito'
        ).order_by('-monto_total')[:limite]
        
        return list(clientes)
    
    @staticmethod
    def flujo_caja_detallado(fecha_inicio, fecha_fin):
        """Análisis detallado de flujo de caja"""
        # Ingresos por ventas de contado
        pagos_contado = CashPayment.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin],
            estado='completado'
        ).aggregate(
            total=Sum('monto'),
            count=Count('id')
        )
        
        # Ingresos por pagos de crédito
        pagos_credito = CreditPayment.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin],
            estado='completado'
        ).aggregate(
            total=Sum('monto_pagado'),
            count=Count('id')
        )
        
        # Desglose por método de pago
        por_metodo = CashPayment.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin],
            estado='completado'
        ).values('metodo').annotate(
            cantidad=Count('id'),
            monto_total=Sum('monto')
        )
        
        por_metodo_credito = CreditPayment.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin],
            estado='completado'
        ).values('metodo').annotate(
            cantidad=Count('id'),
            monto_total=Sum('monto_pagado')
        )
        
        return {
            'pagos_contado': {
                'total': pagos_contado['total'] or 0,
                'cantidad': pagos_contado['count'] or 0
            },
            'pagos_credito': {
                'total': pagos_credito['total'] or 0,
                'cantidad': pagos_credito['count'] or 0
            },
            'total_ingresos': (pagos_contado['total'] or 0) + (pagos_credito['total'] or 0),
            'desglose_metodos': {
                'contado': list(por_metodo),
                'credito': list(por_metodo_credito)
            }
        }
    
    @staticmethod
    def rotacion_inventario(fecha_inicio, fecha_fin):
        """Análisis de rotación de productos"""
        productos = Product.objects.annotate(
            unidades_vendidas=Coalesce(
                Sum('detailnote__cantidad',
                    filter=Q(detailnote__fecha__range=[fecha_inicio, fecha_fin])),
                0
            ),
            ingresos_generados=Coalesce(
                Sum('detailnote__subtotal',
                    filter=Q(detailnote__fecha__range=[fecha_inicio, fecha_fin])),
                Decimal('0')
            ),
            dias_periodo=Value((fecha_fin - fecha_inicio).days or 1, output_field=IntegerField())
        ).annotate(
            rotacion_diaria=ExpressionWrapper(
                F('unidades_vendidas') / F('dias_periodo'),
                output_field=FloatField()
            ),
            dias_inventario=Case(
                When(rotacion_diaria__gt=0, then=ExpressionWrapper(
                    F('stock') / F('rotacion_diaria'),
                    output_field=FloatField()
                )),
                default=Value(999),
                output_field=FloatField()
            )
        ).values(
            'id', 'nombre', 'stock', 'unidades_vendidas',
            'ingresos_generados', 'rotacion_diaria', 'dias_inventario',
            'categoria__descripcion', 'precio'
        ).order_by('dias_inventario')
        
        return list(productos)



# reportes nivel 3

class ReportesAvanzados:
    """Reportes complejos con análisis profundos"""
    
    @staticmethod
    def analisis_rfm_clientes():
        """Segmentación RFM (Recency, Frequency, Monetary) - Compatible con SQLite"""
        try:
            import numpy as np
        except ImportError:
            return {
                'error': 'Se requiere numpy. Instala con: pip install numpy',
                'clientes': [],
                'resumen_segmentos': {}
            }
        
        # Calcular métricas RFM
        hoy = timezone.now().date()
        
        # Obtener clientes con sus métricas básicas
        clientes = Usuario.objects.filter(
            ventas_como_cliente__isnull=False
        ).annotate(
            ultima_compra_fecha=Max('ventas_como_cliente__fecha'),
            frequency=Count('ventas_como_cliente__id', distinct=True),
            monetary=Sum('ventas_como_cliente__monto')
        ).filter(
            frequency__gt=0
        )
        
        # Convertir a lista y agregar valores por defecto
        clientes_list = []
        for cliente in clientes:
            clientes_list.append({
                'id': cliente.id,
                'email': cliente.email,
                'first_name': cliente.first_name or '',
                'last_name': cliente.last_name or '',
                'ultima_compra_fecha': cliente.ultima_compra_fecha,
                'frequency': cliente.frequency,
                'monetary': float(cliente.monetary or 0)
            })
        
        if not clientes_list:
            return {
                'clientes': [],
                'resumen_segmentos': {},
                'mensaje': 'No hay clientes con compras para analizar'
            }
        
        # Calcular recency (días desde última compra)
        for cliente in clientes_list:
            if cliente['ultima_compra_fecha']:
                cliente['recency'] = (hoy - cliente['ultima_compra_fecha']).days
            else:
                cliente['recency'] = 9999
        
        # Extraer valores para calcular scores
        recency_values = [c['recency'] for c in clientes_list]
        frequency_values = [c['frequency'] for c in clientes_list]
        monetary_values = [c['monetary'] for c in clientes_list]
        
        # Función para calcular score de 1-5 basado en quintiles
        def calcular_score(valor, valores, invertir=False):
            """Calcula el score de 1-5 basado en quintiles"""
            valores_unicos = list(set(valores))
            
            if len(valores_unicos) == 1:
                return 3
            
            try:
                quintiles = np.percentile(valores, [20, 40, 60, 80])
            except:
                return 3
            
            if invertir:  # Para recency (menor días = mejor cliente)
                if valor <= quintiles[0]:
                    return 5
                elif valor <= quintiles[1]:
                    return 4
                elif valor <= quintiles[2]:
                    return 3
                elif valor <= quintiles[3]:
                    return 2
                else:
                    return 1
            else:  # Para frequency y monetary (mayor = mejor)
                if valor >= quintiles[3]:
                    return 5
                elif valor >= quintiles[2]:
                    return 4
                elif valor >= quintiles[1]:
                    return 3
                elif valor >= quintiles[0]:
                    return 2
                else:
                    return 1
        
        # Asignar scores a cada cliente
        for cliente in clientes_list:
            cliente['r_score'] = calcular_score(cliente['recency'], recency_values, invertir=True)
            cliente['f_score'] = calcular_score(cliente['frequency'], frequency_values)
            cliente['m_score'] = calcular_score(cliente['monetary'], monetary_values)
            cliente['rfm_total'] = cliente['r_score'] + cliente['f_score'] + cliente['m_score']
            
            # Asignar segmento basado en scores
            r = cliente['r_score']
            f = cliente['f_score']
            m = cliente['m_score']
            
            if r >= 4 and f >= 4 and m >= 4:
                segmento = 'Champions'
            elif r >= 3 and f >= 3 and m >= 3:
                segmento = 'Leales'
            elif r >= 4 and f <= 2:
                segmento = 'Nuevos Prometedores'
            elif r <= 2 and f >= 4:
                segmento = 'En Riesgo'
            elif r <= 2 and f <= 2:
                segmento = 'Perdidos'
            else:
                segmento = 'Normales'
            
            cliente['segmento'] = segmento
        
        # Ordenar por RFM total
        clientes_list.sort(key=lambda x: x['rfm_total'], reverse=True)
        
        # Calcular resumen por segmento
        resumen_segmentos = {}
        for cliente in clientes_list:
            seg = cliente['segmento']
            if seg not in resumen_segmentos:
                resumen_segmentos[seg] = {
                    'cantidad': 0,
                    'valor_total': 0.0,
                    'frecuencia_promedio': 0.0
                }
            
            resumen_segmentos[seg]['cantidad'] += 1
            resumen_segmentos[seg]['valor_total'] += cliente['monetary']
            resumen_segmentos[seg]['frecuencia_promedio'] += cliente['frequency']
        
        # Calcular promedios
        for seg in resumen_segmentos:
            cantidad = resumen_segmentos[seg]['cantidad']
            if cantidad > 0:
                resumen_segmentos[seg]['frecuencia_promedio'] = round(
                    resumen_segmentos[seg]['frecuencia_promedio'] / cantidad, 2
                )
            resumen_segmentos[seg]['valor_total'] = round(resumen_segmentos[seg]['valor_total'], 2)
        
        return {
            'clientes': clientes_list,
            'resumen_segmentos': resumen_segmentos,
            'total_clientes_analizados': len(clientes_list)
        }
    
    @staticmethod
    def analisis_tendencias_ventas(meses=12):
        """Análisis de tendencias con comparaciones mes a mes"""
        fecha_inicio = timezone.now().date() - timedelta(days=meses*30)
        
        ventas_mensuales = SalesNote.objects.filter(
            fecha__gte=fecha_inicio
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            num_ventas=Count('id'),
            ingresos=Sum('monto'),
            ticket_promedio=Avg('monto'),
            ventas_contado=Count('id', filter=Q(tipo_pago='contado')),
            ventas_credito=Count('id', filter=Q(tipo_pago='credito'))
        ).order_by('mes')
        
        # Calcular crecimientos
        datos = list(ventas_mensuales)
        for i in range(1, len(datos)):
            if datos[i-1]['ingresos']:
                datos[i]['crecimiento_ingresos'] = (
                    (datos[i]['ingresos'] - datos[i-1]['ingresos']) / 
                    datos[i-1]['ingresos'] * 100
                )
            else:
                datos[i]['crecimiento_ingresos'] = 0
                
            if datos[i-1]['num_ventas']:
                datos[i]['crecimiento_ventas'] = (
                    (datos[i]['num_ventas'] - datos[i-1]['num_ventas']) / 
                    datos[i-1]['num_ventas'] * 100
                )
            else:
                datos[i]['crecimiento_ventas'] = 0
        
        return datos
    
    @staticmethod
    def analisis_cohortes_retencion(meses=6):
        """Análisis de retención de clientes por cohortes"""
        fecha_inicio = timezone.now().date() - timedelta(days=meses*30)
        
        # Primera compra de cada cliente
        primeras_compras = Usuario.objects.filter(
            ventas_como_cliente__fecha__gte=fecha_inicio
        ).annotate(
            mes_cohorte=TruncMonth(Min('ventas_como_cliente__fecha'))
        ).values('id', 'mes_cohorte')
        
        # Construir diccionario de cohortes
        cohortes = {}
        for pc in primeras_compras:
            mes = pc['mes_cohorte']
            if mes:
                if mes not in cohortes:
                    cohortes[mes] = set()
                cohortes[mes].add(pc['id'])
        
        # Calcular retención por mes
        resultado = []
        for mes_cohorte, clientes_cohorte in cohortes.items():
            tamaño_cohorte = len(clientes_cohorte)
            datos_cohorte = {'mes_cohorte': mes_cohorte, 'tamaño': tamaño_cohorte, 'meses': {}}
            
            for i in range(6):
                mes_target = mes_cohorte + timedelta(days=30*i)
                clientes_activos = Usuario.objects.filter(
                    id__in=clientes_cohorte,
                    ventas_como_cliente__fecha__month=mes_target.month,
                    ventas_como_cliente__fecha__year=mes_target.year
                ).distinct().count()
                
                if tamaño_cohorte > 0:
                    tasa = (clientes_activos / tamaño_cohorte) * 100
                else:
                    tasa = 0
                    
                datos_cohorte['meses'][i] = {
                    'activos': clientes_activos,
                    'tasa_retencion': round(tasa, 1)
                }
            
            resultado.append(datos_cohorte)
        
        return sorted(resultado, key=lambda x: x['mes_cohorte'])
    
    @staticmethod
    def analisis_cartera_creditos():
        """Análisis detallado de cartera de créditos"""
        creditos_activos = CreditSale.objects.filter(estado='activo')
        
        # Análisis por antigüedad
        hoy = timezone.now().date()
        analisis_edad = creditos_activos.annotate(
            dias_transcurridos=ExpressionWrapper(
                Value(hoy) - F('fecha_inicial'),
                output_field=IntegerField()
            ),
            dias_para_vencer=ExpressionWrapper(
                F('fecha_vencimiento') - Value(hoy),
                output_field=IntegerField()
            )
        ).aggregate(
            total_creditos=Count('id'),
            monto_total=Sum('saldo_pendiente'),
            por_vencer_30_dias=Count('id', filter=Q(fecha_vencimiento__lte=hoy + timedelta(days=30))),
            monto_por_vencer=Sum('saldo_pendiente', filter=Q(fecha_vencimiento__lte=hoy + timedelta(days=30))),
            vencidos=Count('id', filter=Q(fecha_vencimiento__lt=hoy)),
            monto_vencido=Sum('saldo_pendiente', filter=Q(fecha_vencimiento__lt=hoy))
        )
        
        # Análisis por cliente
        clientes_con_credito = Usuario.objects.filter(
            ventas_como_cliente__creditos__estado='activo'
        ).annotate(
            num_creditos=Count('ventas_como_cliente__creditos'),
            saldo_total=Sum('ventas_como_cliente__creditos__saldo_pendiente'),
            credito_mas_antiguo=Min('ventas_como_cliente__creditos__fecha_inicial')
        ).values(
            'id', 'email', 'first_name', 'last_name', 'telefono',
            'num_creditos', 'saldo_total', 'credito_mas_antiguo', 'estado_credito'
        ).order_by('-saldo_total')
        
        # Cuotas pendientes próximas
        cuotas_proximas = CreditInstallment.objects.filter(
            pagado=False,
            fecha_vencimiento__lte=hoy + timedelta(days=15)
        ).select_related('venta_credito__nota_venta__cliente').values(
            'venta_credito__nota_venta__cliente__email',
            'venta_credito__nota_venta__cliente__first_name',
            'venta_credito__nota_venta__cliente__telefono',
            'numero',
            'fecha_vencimiento',
            'monto'
        ).order_by('fecha_vencimiento')
        
        return {
            'resumen': analisis_edad,
            'clientes': list(clientes_con_credito),
            'cuotas_proximas': list(cuotas_proximas)
        }
    
    @staticmethod
    def market_basket_analysis(fecha_inicio, fecha_fin, min_soporte=3):
        """Análisis de productos que se compran juntos"""
        from collections import defaultdict
        
        # Obtener todas las ventas del período
        ventas = SalesNote.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin]
        ).prefetch_related('detalles__producto')
        
        # Construir combinaciones de productos
        combinaciones = defaultdict(int)
        productos_por_venta = {}
        
        for venta in ventas:
            productos = [d.producto for d in venta.detalles.all()]
            productos_por_venta[venta.id] = productos
            
            # Generar pares de productos
            for i in range(len(productos)):
                for j in range(i+1, len(productos)):
                    par = tuple(sorted([productos[i].id, productos[j].id]))
                    combinaciones[par] += 1
        
        # Calcular métricas de asociación
        total_ventas = len(ventas)
        asociaciones = []
        
        for (prod_a_id, prod_b_id), frecuencia in combinaciones.items():
            if frecuencia >= min_soporte:
                prod_a = Product.objects.get(id=prod_a_id)
                prod_b = Product.objects.get(id=prod_b_id)
                
                # Soporte: frecuencia de aparición conjunta
                soporte = frecuencia / total_ventas
                
                # Confianza: P(B|A)
                ventas_con_a = sum(1 for prods in productos_por_venta.values() if prod_a in prods)
                confianza = frecuencia / ventas_con_a if ventas_con_a > 0 else 0
                
                # Lift: indica si la asociación es significativa
                ventas_con_b = sum(1 for prods in productos_por_venta.values() if prod_b in prods)
                prob_b = ventas_con_b / total_ventas if total_ventas > 0 else 0
                lift = confianza / prob_b if prob_b > 0 else 0
                
                if lift > 1.2:  # Solo asociaciones significativas
                    asociaciones.append({
                        'producto_a': {'id': prod_a.id, 'nombre': prod_a.nombre},
                        'producto_b': {'id': prod_b.id, 'nombre': prod_b.nombre},
                        'frecuencia': frecuencia,
                        'soporte': round(soporte * 100, 2),
                        'confianza': round(confianza * 100, 2),
                        'lift': round(lift, 2)
                    })
        
        return sorted(asociaciones, key=lambda x: x['lift'], reverse=True)


class GeneradorReportes:
    """Sistema flexible para generar cualquier reporte"""
    
    def __init__(self, modelo_base=None):
        self.modelo = modelo_base or SalesNote
        self.filtros = Q()
        self.agrupaciones = []
        self.anotaciones = {}
        self.ordenamiento = []
    
    def agregar_filtro(self, **kwargs):
        """Agregar filtros dinámicamente"""
        self.filtros &= Q(**kwargs)
        return self
    
    def agregar_filtro_q(self, q_object):
        """Agregar objetos Q complejos"""
        self.filtros &= q_object
        return self
    
    def agrupar_por(self, *campos):
        """Definir agrupaciones"""
        self.agrupaciones.extend(campos)
        return self
    
    def agregar_metrica(self, nombre, expresion):
        """Agregar métricas calculadas"""
        self.anotaciones[nombre] = expresion
        return self
    
    def ordenar_por(self, *campos):
        """Definir ordenamiento"""
        self.ordenamiento.extend(campos)
        return self
    
    def ejecutar(self):
        """Ejecutar el reporte"""
        queryset = self.modelo.objects.filter(self.filtros)
        
        if self.agrupaciones:
            queryset = queryset.values(*self.agrupaciones)
        
        if self.anotaciones:
            queryset = queryset.annotate(**self.anotaciones)
        
        if self.ordenamiento:
            queryset = queryset.order_by(*self.ordenamiento)
        
        return list(queryset)