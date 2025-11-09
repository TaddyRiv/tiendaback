from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from ventas.models import SalesNote, DetailNote, CashPayment
from productos.models import Product

from ventas.models import SalesNote, DetailNote, CashPayment
from productos.models import Product
from creditos.models import CreditConfig, CreditSale, CreditInstallment


class DetailNoteSerializer(serializers.ModelSerializer):
    # para crear: usar producto_id; para leer: producto embebido simple
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='producto', write_only=True
    )

    class Meta:
        model = DetailNote
        fields = ['id', 'nota', 'producto', 'producto_id', 'fecha', 'cantidad', 'subtotal']
        read_only_fields = ['id', 'nota', 'fecha', 'producto']


class SalesNoteSerializer(serializers.ModelSerializer):
    detalles = DetailNoteSerializer(many=True, write_only=True)

    class Meta:
        model = SalesNote
        fields = ['id', 'cliente', 'empleado', 'fecha', 'monto', 'tipo_pago', 'estado',
                  'created_at', 'updated_at', 'detalles']
        read_only_fields = ['id', 'fecha', 'estado', 'created_at', 'updated_at']

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles', [])

        # --- Abrimos una transacción atómica ---
        with transaction.atomic():
            nota = SalesNote.objects.create(**validated_data)

            total_calculado = Decimal('0')
            for d in detalles_data:
                producto = d['producto']
                cantidad = d['cantidad']
                subtotal = d['subtotal']

                # --- Verificar stock disponible ---
                if producto.stock < cantidad:
                    raise serializers.ValidationError(
                        f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}, solicitado: {cantidad}."
                    )

                # --- Crear el detalle ---
                DetailNote.objects.create(
                    nota=nota,
                    producto=producto,
                    cantidad=cantidad,
                    subtotal=subtotal
                )

                # --- Restar stock del producto ---
                producto.stock -= cantidad
                producto.save(update_fields=['stock'])

                total_calculado += Decimal(subtotal)

            # --- Flujo de pago ---
            if nota.tipo_pago == "efectivo":
                CashPayment.objects.create(
                    nota=nota,
                    monto=nota.monto,
                    metodo='efectivo',
                    estado='completado'
                )
                nota.estado = "completada"
                nota.save(update_fields=['estado'])

            else:  # tipo crédito
                nota.estado = "pendiente"
                nota.save(update_fields=['estado'])

                config = CreditConfig.objects.first()
                if not config:
                    raise serializers.ValidationError("No existe configuración de crédito (CreditConfig).")

                interes = Decimal(config.tasa_interes) / Decimal('100')
                total_con_interes = (Decimal(nota.monto) * (Decimal('1') + interes)).quantize(Decimal('0.01'))

                credito = CreditSale.objects.create(
                    nota_venta=nota,
                    total_original=nota.monto,
                    total_con_intereses=total_con_interes,
                    tasa_aplicada=config.tasa_interes,
                    saldo_pendiente=total_con_interes,
                    estado="activo",
                    fecha_inicial=timezone.now().date(),
                    fecha_vencimiento=timezone.now().date() + timedelta(
                        days=config.cantidad_cuotas * config.dias_entre_cuotas
                    )
                )

                monto_cuota = (total_con_interes / Decimal(config.cantidad_cuotas)).quantize(Decimal('0.01'))
                for i in range(1, config.cantidad_cuotas + 1):
                    CreditInstallment.objects.create(
                        venta_credito=credito,
                        numero=i,
                        fecha_vencimiento=timezone.now().date() + timedelta(days=i * config.dias_entre_cuotas),
                        monto=monto_cuota,
                        pagado=False
                    )

        return nota

class ProductoSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'nombre']  # Solo lo necesario

class DetalleVentaSerializer(serializers.ModelSerializer):
    producto = ProductoSimpleSerializer(read_only=True)  # ✅ incluir nombre del producto

    class Meta:
        model = DetailNote
        fields = ['id', 'nota', 'producto', 'fecha', 'cantidad', 'subtotal']