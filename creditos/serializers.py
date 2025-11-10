from rest_framework import serializers
from creditos.models import (
    CreditConfig,
    CreditSale,
    CreditInstallment,
    CreditPayment
)


class CreditConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditConfig
        fields = '__all__'


class CreditPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditPayment
        fields = [
            'id', 'cuota', 'fecha', 'monto_pagado',
            'metodo', 'estado', 'created_at'
        ]
        read_only_fields = ['id', 'fecha', 'created_at']

class CreditInstallmentSerializer(serializers.ModelSerializer):
    pagos = CreditPaymentSerializer(many=True, read_only=True) 

    class Meta:
        model = CreditInstallment
        fields = [
            'id', 'venta_credito', 'numero', 'cuota',
            'fecha_vencimiento', 'monto', 'pagado',
            'fecha_pago', 'pagos'
        ]
        read_only_fields = ['id', 'pagado', 'fecha_pago']


class CreditSaleSerializer(serializers.ModelSerializer):
    cuotas = CreditInstallmentSerializer(many=True, read_only=True)

    class Meta:
        model = CreditSale
        fields = [
            'id', 'nota_venta', 'total_original', 'total_con_intereses',
            'tasa_aplicada', 'saldo_pendiente', 'estado',
            'fecha_inicial', 'fecha_vencimiento', 'cuotas'
        ]
        read_only_fields = ['id', 'estado', 'fecha_inicial', 'fecha_vencimiento']
