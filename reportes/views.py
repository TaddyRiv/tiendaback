from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta
from .reportes_niveles import (
    ReportesBasicos, ReportesIntermedios, ReportesAvanzados, GeneradorReportes
)
from django.core.cache import cache
from rest_framework import generics
from django.db.models import Sum, Count, Avg
from django.db.models import Max, Min
from .models import HistorialReporte
from .serializers import HistorialReporteSerializer

class ReportesRootView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            "message": "📊 Bienvenido al sistema de reportes",
            "endpoints_disponibles": [
                "ventas-periodo/",
                "top-productos/",
                "bajo-stock/",
                "ventas-diarias/",
                "resumen-creditos/",
                "analisis-categorias/",
                "rendimiento-empleados/",
                "clientes-frecuentes/",
                "flujo-caja/",
                "rotacion-inventario/",
                "rfm/",
                "tendencias/",
                "cohortes/",
                "cartera-creditos/",
                "market-basket/",
                "dashboard/",
                "dinamico/",
                "exportar/",
                "historial/"
            ]
        })

class LimpiarCacheView(APIView):
    permission_classes = [IsAuthenticated]  
    def delete(self, request):
        cache.clear()
        return Response({'message': 'Cache limpiada exitosamente.'}, status=status.HTTP_200_OK)

class HistorialReportesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HistorialReporteSerializer

    def get_queryset(self):
        # Filtra solo los reportes del usuario actual
        return HistorialReporte.objects.filter(usuario=self.request.user)
    

class VentasPorPeriodoView(APIView):
    """
    GET /api/reportes/ventas-periodo/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response({
                'error': 'Se requieren fecha_inicio y fecha_fin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reporte = ReportesBasicos.ventas_por_periodo(fecha_inicio, fecha_fin)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TopProductosView(APIView):
    """
    GET /api/reportes/top-productos/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31&limite=10
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        limite = int(request.query_params.get('limite', 10))
        
        if not fecha_inicio or not fecha_fin:
            return Response({
                'error': 'Se requieren fecha_inicio y fecha_fin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reporte = ReportesBasicos.top_productos(fecha_inicio, fecha_fin, limite)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductosBajoStockView(APIView):
    """
    GET /api/reportes/bajo-stock/?minimo=10
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        minimo = int(request.query_params.get('minimo', 10))
        
        try:
            reporte = ReportesBasicos.productos_bajo_stock(minimo)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VentasPorDiaView(APIView):
    """
    GET /api/reportes/ventas-diarias/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response({
                'error': 'Se requieren fecha_inicio y fecha_fin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reporte = ReportesBasicos.ventas_por_dia(fecha_inicio, fecha_fin)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumenCreditosView(APIView):
    """
    GET /api/reportes/resumen-creditos/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            reporte = ReportesBasicos.resumen_creditos()
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalisisCategoriaView(APIView):
    """
    GET /api/reportes/analisis-categorias/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response({
                'error': 'Se requieren fecha_inicio y fecha_fin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reporte = ReportesIntermedios.analisis_por_categoria(fecha_inicio, fecha_fin)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RendimientoEmpleadosView(APIView):
    """
    GET /api/reportes/rendimiento-empleados/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response({
                'error': 'Se requieren fecha_inicio y fecha_fin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reporte = ReportesIntermedios.rendimiento_empleados(fecha_inicio, fecha_fin)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientesFrecuentesView(APIView):
    """
    GET /api/reportes/clientes-frecuentes/?limite=20
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        limite = int(request.query_params.get('limite', 20))
        
        try:
            reporte = ReportesIntermedios.analisis_clientes_frecuentes(limite)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FlujoCajaView(APIView):
    """
    GET /api/reportes/flujo-caja/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response({
                'error': 'Se requieren fecha_inicio y fecha_fin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reporte = ReportesIntermedios.flujo_caja_detallado(fecha_inicio, fecha_fin)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RotacionInventarioView(APIView):
    """
    GET /api/reportes/rotacion-inventario/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response({
                'error': 'Se requieren fecha_inicio y fecha_fin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reporte = ReportesIntermedios.rotacion_inventario(fecha_inicio, fecha_fin)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalisisRFMView(APIView):
    """
    GET /api/reportes/rfm/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            reporte = ReportesAvanzados.analisis_rfm_clientes()
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TendenciasVentasView(APIView):
    """
    GET /api/reportes/tendencias/?meses=12
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        meses = int(request.query_params.get('meses', 12))
        
        try:
            reporte = ReportesAvanzados.analisis_tendencias_ventas(meses)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CohortesRetencionView(APIView):
    """
    GET /api/reportes/cohortes/?meses=6
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        meses = int(request.query_params.get('meses', 6))
        
        try:
            reporte = ReportesAvanzados.analisis_cohortes_retencion(meses)
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CarteraCreditosView(APIView):
    """
    GET /api/reportes/cartera-creditos/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            reporte = ReportesAvanzados.analisis_cartera_creditos()
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketBasketView(APIView):
    """
    GET /api/reportes/market-basket/?fecha_inicio=2024-01-01&fecha_fin=2024-12-31&min_soporte=3
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        min_soporte = int(request.query_params.get('min_soporte', 3))
        
        if not fecha_inicio or not fecha_fin:
            return Response({
                'error': 'Se requieren fecha_inicio y fecha_fin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reporte = ReportesAvanzados.market_basket_analysis(
                fecha_inicio, fecha_fin, min_soporte
            )
            return Response(reporte, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardCompletoView(APIView):
    """
    GET /api/reportes/dashboard/?periodo=mes_actual
    
    Periodos disponibles: hoy, semana_actual, mes_actual, mes_anterior, trimestre, año
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        periodo = request.query_params.get('periodo', 'mes_actual')
        
        # Calcular fechas según período
        hoy = timezone.now().date()
        
        if periodo == 'hoy':
            fecha_inicio = fecha_fin = hoy
        elif periodo == 'semana_actual':
            fecha_inicio = hoy - timedelta(days=hoy.weekday())
            fecha_fin = hoy
        elif periodo == 'mes_actual':
            fecha_inicio = hoy.replace(day=1)
            fecha_fin = hoy
        elif periodo == 'mes_anterior':
            primer_dia_mes_actual = hoy.replace(day=1)
            fecha_fin = primer_dia_mes_actual - timedelta(days=1)
            fecha_inicio = fecha_fin.replace(day=1)
        elif periodo == 'trimestre':
            fecha_inicio = hoy - timedelta(days=90)
            fecha_fin = hoy
        elif periodo == 'año':
            fecha_inicio = hoy.replace(month=1, day=1)
            fecha_fin = hoy
        else:
            return Response({
                'error': 'Período no válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            dashboard = {
                'periodo': {
                    'descripcion': periodo,
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                },
                'ventas': ReportesBasicos.ventas_por_periodo(fecha_inicio, fecha_fin),
                'top_productos': ReportesBasicos.top_productos(fecha_inicio, fecha_fin, 5),
                'creditos': ReportesBasicos.resumen_creditos(),
                'bajo_stock': ReportesBasicos.productos_bajo_stock(10),
                'categorias': ReportesIntermedios.analisis_por_categoria(fecha_inicio, fecha_fin),
                'clientes_top': ReportesIntermedios.analisis_clientes_frecuentes(10)
            }
            
            return Response(dashboard, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReporteDinamicoView(APIView):
    """
    POST /api/reportes/dinamico/
    
    Body ejemplo:
    {
        "modelo": "ventas",
        "filtros": {
            "fecha__gte": "2024-01-01",
            "fecha__lte": "2024-01-31",
            "tipo_pago": "contado"
        },
        "agrupar_por": ["empleado__email"],
        "metricas": {
            "total_ventas": {"tipo": "count", "campo": "id"},
            "ingresos": {"tipo": "sum", "campo": "monto"},
            "ticket_promedio": {"tipo": "avg", "campo": "monto"}
        },
        "ordenar_por": ["-ingresos"]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from ventas.models import SalesNote, DetailNote
        from productos.models import Product
        from usuarios.models import Usuario
        
        # Mapeo de modelos
        MODELOS = {
            'ventas': SalesNote,
            'detalles': DetailNote,
            'productos': Product,
            'usuarios': Usuario
        }
        
        try:
            data = request.data
            modelo_nombre = data.get('modelo', 'ventas')
            
            if modelo_nombre not in MODELOS:
                return Response({
                    'error': f'Modelo no válido. Opciones: {list(MODELOS.keys())}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            generador = GeneradorReportes(MODELOS[modelo_nombre])
            
            # Aplicar filtros
            filtros = data.get('filtros', {})
            if filtros:
                generador.agregar_filtro(**filtros)
            
            # Aplicar agrupaciones
            agrupar = data.get('agrupar_por', [])
            if agrupar:
                generador.agrupar_por(*agrupar)
            
            # Aplicar métricas
            metricas = data.get('metricas', {})
            FUNCIONES = {
                'sum': Sum,
                'count': Count,
                'avg': Avg,
                'max': Max,
                'min': Min
            }
            
            for nombre, config in metricas.items():
                tipo = config.get('tipo', 'count').lower()
                campo = config.get('campo')
                
                if tipo not in FUNCIONES:
                    continue
                
                if campo:
                    expresion = FUNCIONES[tipo](campo)
                else:
                    expresion = FUNCIONES[tipo]('id')
                
                generador.agregar_metrica(nombre, expresion)
            
            # Aplicar ordenamiento
            ordenar = data.get('ordenar_por', [])
            if ordenar:
                generador.ordenar_por(*ordenar)
            
            # Ejecutar
            resultado = generador.ejecutar()
            
            resumen = None
            if isinstance(resultado, list) and len(resultado) > 0:
                resumen = f"{len(resultado)} filas devueltas."
            elif isinstance(resultado, dict):
                resumen = ", ".join([f"{k}: {v}" for k, v in resultado.items()])

            # --- Guardar en historial ---
            HistorialReporte.objects.create(
                usuario=request.user,
                tipo=f"Reporte dinámico ({data.get('modelo', 'sin modelo')})",
                parametros=data,
                resultado_resumen=resumen
            )

            return Response({
                'modelo': modelo_nombre,
                'total_registros': len(resultado) if isinstance(resultado, list) else 1,
                'resumen': resumen,
                'datos': resultado
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExportarReporteView(APIView):
    """
    POST /api/reportes/exportar/
    
    Body:
    {
        "tipo_reporte": "ventas_periodo",
        "parametros": {
            "fecha_inicio": "2024-01-01",
            "fecha_fin": "2024-01-31"
        },
        "formato": "excel"  // opciones: excel, csv, pdf
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        import pandas as pd
        from django.http import HttpResponse
        import io
        
        data = request.data
        tipo_reporte = data.get('tipo_reporte')
        parametros = data.get('parametros', {})
        formato = data.get('formato', 'excel')
        
        # Mapeo de reportes
        REPORTES = {
            'ventas_periodo': lambda: ReportesBasicos.ventas_por_periodo(
                parametros['fecha_inicio'], parametros['fecha_fin']
            ),
            'top_productos': lambda: ReportesBasicos.top_productos(
                parametros['fecha_inicio'], parametros['fecha_fin'],
                parametros.get('limite', 10)
            ),
            'rfm': lambda: ReportesAvanzados.analisis_rfm_clientes()
        }
        
        if tipo_reporte not in REPORTES:
            return Response({
                'error': 'Tipo de reporte no válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            datos = REPORTES[tipo_reporte]()
            
            # Convertir a DataFrame
            if isinstance(datos, dict):
                if 'clientes' in datos:
                    df = pd.DataFrame(datos['clientes'])
                else:
                    df = pd.DataFrame([datos])
            else:
                df = pd.DataFrame(datos)
            
            # Exportar según formato
            if formato == 'excel':
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Reporte')
                output.seek(0)
                
                response = HttpResponse(
                    output.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename=reporte_{tipo_reporte}.xlsx'
                return response
            
            elif formato == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename=reporte_{tipo_reporte}.csv'
                df.to_csv(response, index=False)
                return response
            
            else:
                return Response({
                    'error': 'Formato no soportado'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)