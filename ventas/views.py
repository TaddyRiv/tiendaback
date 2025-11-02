from rest_framework import viewsets, permissions
from ventas.models import SalesNote, DetailNote, CashPayment
from ventas.serializers import SalesNoteSerializer, DetailNoteSerializer
from rest_framework.response import Response


class SalesNoteViewSet(viewsets.ModelViewSet):
    queryset = SalesNote.objects.all().select_related('cliente', 'empleado')
    serializer_class = SalesNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        # Devolver stock antes de eliminar
        detalles = instance.detalles.all()
        for d in detalles:
            producto = d.producto
            producto.stock += d.cantidad
            producto.save(update_fields=['stock'])
        instance.delete()

class DetailNoteViewSet(viewsets.ModelViewSet):
    queryset = DetailNote.objects.select_related('nota', 'producto').all()
    serializer_class = DetailNoteSerializer
    permission_classes = [permissions.IsAuthenticated]


class CashPaymentViewSet(viewsets.ModelViewSet):
    queryset = CashPayment.objects.select_related('nota').all()
    serializer_class = None  # si más adelante quieres CRUD de pagos contado, define su serializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return Response({"detail": "Endpoint de pagos al contado (CRUD opcional)."})
