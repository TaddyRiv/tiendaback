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

    @action(detail=True, methods=['post'])
    def pagar(self, request, pk=None):
        cuota = self.get_object()
        if cuota.pagado:
            return Response({"detail": "Esta cuota ya fue pagada."}, status=400)

        monto = Decimal(request.data.get('monto', cuota.monto))
        metodo = request.data.get('metodo', 'efectivo')

        CreditPayment.objects.create(
            cuota=cuota,
            monto_pagado=monto,
            metodo=metodo,
            estado='completado'
        )

        cuota.pagado = True
        cuota.fecha_pago = timezone.now().date()
        cuota.save(update_fields=['pagado', 'fecha_pago'])

        credito = cuota.venta_credito
        credito.saldo_pendiente -= monto
        if credito.saldo_pendiente <= 0:
            credito.estado = 'pagado'
        credito.save(update_fields=['saldo_pendiente', 'estado'])

        return Response({
            "detail": "Pago registrado exitosamente.",
            "cuota_id": cuota.id,
            "nuevo_saldo": str(credito.saldo_pendiente),
            "estado_credito": credito.estado
        })
