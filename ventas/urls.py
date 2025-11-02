from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ventas.views import SalesNoteViewSet, DetailNoteViewSet, CashPaymentViewSet

router = DefaultRouter()
router.register(r'ventas', SalesNoteViewSet, basename='ventas')
router.register(r'detalles', DetailNoteViewSet, basename='detalles')
router.register(r'pagos', CashPaymentViewSet, basename='pagos')

urlpatterns = [
    path('', include(router.urls)),
]
