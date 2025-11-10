from httpx import request
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from decimal import Decimal
from creditos.models import CreditInstallment, CreditPayment
from creditos.serializers import CreditInstallmentSerializer

class CreditInstallmentViewSet(viewsets.ModelViewSet):
    queryset = CreditInstallment.objects.select_related('venta_credito')
    serializer_class = CreditInstallmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='venta/(?P<venta_id>[^/.]+)')
    def cuotas_por_venta(self, request, venta_id=None):
        cuotas = self.queryset.filter(venta_credito__nota_venta_id=venta_id)
        serializer = self.get_serializer(cuotas, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['post'])
    def pagar(self, request, pk=None):
        cuota = self.get_object()
        if cuota.pagado:
            return Response({"detail": "Esta cuota ya fue pagada."}, status=400)

        try:
            monto = Decimal(request.data.get('monto') or cuota.monto)
        except Exception:
            return Response({"detail": "Monto inválido."}, status=400)

        metodo = request.data.get('metodo', 'efectivo')

    # Registrar pago
        CreditPayment.objects.create(
            cuota=cuota,
            monto_pagado=monto,
            metodo=metodo,
            estado='completado'
        )  

    # Actualizar cuota
        cuota.pagado = True
        cuota.fecha_pago = timezone.now().date()
        cuota.save(update_fields=['pagado', 'fecha_pago'])

    # Actualizar saldo del crédito
        credito = cuota.venta_credito
        credito.saldo_pendiente = max(Decimal('0.00'), credito.saldo_pendiente - monto)
        if credito.saldo_pendiente <= 0:
           credito.estado = 'pagado'
        credito.save(update_fields=['saldo_pendiente', 'estado'])

        return Response({
           "detail": "Pago registrado exitosamente.",
           "cuota_id": cuota.id,
           "nuevo_saldo": str(credito.saldo_pendiente),
           "estado_credito": credito.estado
        }, status=200)
