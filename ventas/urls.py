from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ventas.views import SalesNoteViewSet, DetailNoteViewSet, CashPaymentViewSet
from ventas.views import StripeCreateIntentView, StripeWebhookView

router = DefaultRouter()
router.register(r'ventas', SalesNoteViewSet, basename='ventas')
router.register(r'detalles', DetailNoteViewSet, basename='detalles')
router.register(r'pagos', CashPaymentViewSet, basename='pagos')

urlpatterns = [
    path('', include(router.urls)),
    path('pagos/stripe/create-intent/', StripeCreateIntentView.as_view(), name='stripe-create-intent'),
    path('pagos/stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
