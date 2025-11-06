from django.urls import path
from django.urls import include
from reportes import views
from .views import (
    # Reportes Básicos
    ProbarTranscripcionView,
    ReportesPorVozView,
    ReportesTextoView,
    VentasPorPeriodoView,
    TopProductosView,
    ProductosBajoStockView,
    VentasPorDiaView,
    ResumenCreditosView,
    
    # Reportes Intermedios
    AnalisisCategoriaView,
    RendimientoEmpleadosView,
    ClientesFrecuentesView,
    FlujoCajaView,
    RotacionInventarioView,
    
    # Reportes Avanzados
    AnalisisRFMView,
    TendenciasVentasView,
    CohortesRetencionView,
    CarteraCreditosView,
    MarketBasketView,
    
    # Dashboard y Dinámicos
    DashboardCompletoView,
    ReporteDinamicoView,
    ExportarReporteView,
    ReportesRootView,
    
)

urlpatterns = [
    path('', ReportesRootView.as_view(), name='reportes-root'),
    path('ventas-periodo/', VentasPorPeriodoView.as_view(), name='ventas-periodo'),
    path('top-productos/', TopProductosView.as_view(), name='top-productos'),
    path('bajo-stock/', ProductosBajoStockView.as_view(), name='bajo-stock'),
    path('ventas-diarias/', VentasPorDiaView.as_view(), name='ventas-diarias'),
    path('resumen-creditos/', ResumenCreditosView.as_view(), name='resumen-creditos'),
    

    path('analisis-categorias/', AnalisisCategoriaView.as_view(), name='analisis-categorias'),
    path('rendimiento-empleados/', RendimientoEmpleadosView.as_view(), name='rendimiento-empleados'),
    path('clientes-frecuentes/', ClientesFrecuentesView.as_view(), name='clientes-frecuentes'),
    path('flujo-caja/', FlujoCajaView.as_view(), name='flujo-caja'),
    path('rotacion-inventario/', RotacionInventarioView.as_view(), name='rotacion-inventario'),
    

    path('rfm/', AnalisisRFMView.as_view(), name='rfm'),
    path('tendencias/', TendenciasVentasView.as_view(), name='tendencias'),
    path('cohortes/', CohortesRetencionView.as_view(), name='cohortes'),
    path('cartera-creditos/', CarteraCreditosView.as_view(), name='cartera-creditos'),
    path('market-basket/', MarketBasketView.as_view(), name='market-basket'),
    

    path('dashboard/', DashboardCompletoView.as_view(), name='dashboard'),
    path('dinamico/', ReporteDinamicoView.as_view(), name='dinamico'),
    path('exportar/', ExportarReporteView.as_view(), name='exportar'),

    path('historial/', views.HistorialReportesView.as_view(), name='historial_reportes'),

    path('voz/', ReportesPorVozView.as_view(), name='voz'),
    path('texto/', ReportesTextoView.as_view(), name='texto'),
    path('probar-audio/', ProbarTranscripcionView.as_view(), name='probar-audio'),

]
