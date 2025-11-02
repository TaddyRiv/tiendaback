from django.db import models
from ventas.models import SalesNote

class CreditConfig(models.Model):
    monto_max = models.DecimalField(max_digits=10, decimal_places=2)
    tasa_interes = models.DecimalField(max_digits=5, decimal_places=2)
    cantidad_cuotas = models.PositiveIntegerField(default=3)
    dias_entre_cuotas = models.PositiveIntegerField(default=10)
    creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'credit_config'
        verbose_name = 'Configuración de Crédito'
        verbose_name_plural = 'Configuraciones de Crédito'

    def __str__(self):
        return f"Config - {self.tasa_interes}% / Máx: {self.monto_max}"


class CreditSale(models.Model):
    nota_venta = models.ForeignKey(SalesNote,on_delete=models.CASCADE,related_name='creditos')
    total_original = models.DecimalField(max_digits=10, decimal_places=2)
    total_con_intereses = models.DecimalField(max_digits=10, decimal_places=2)
    tasa_aplicada = models.DecimalField(max_digits=5, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('activo', 'Activo'),
            ('pagado', 'Pagado'),
            ('atrasado', 'Atrasado')
        ],
        default='activo'
    )
    fecha_inicial = models.DateField()
    fecha_vencimiento = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'credit_sale'
        verbose_name = 'Venta a Crédito'
        verbose_name_plural = 'Ventas a Crédito'
        ordering = ['-fecha_inicial']

    def __str__(self):
        return f"Crédito #{self.id} - {self.nota_venta.id}"


class CreditInstallment(models.Model):
    venta_credito = models.ForeignKey(
        CreditSale,
        on_delete=models.CASCADE,
        related_name='cuotas'
    )
    numero = models.PositiveIntegerField()
    cuota = models.CharField(max_length=50, blank=True, null=False)
    fecha_vencimiento = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'credit_installment'
        verbose_name = 'Cuota de Crédito'
        verbose_name_plural = 'Cuotas de Crédito'
        ordering = ['numero']

    def __str__(self):
        return f"Cuota {self.numero} - Crédito #{self.venta_credito.id}"


class CreditPayment(models.Model):
    cuota = models.ForeignKey(
        CreditInstallment,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    fecha = models.DateField(auto_now_add=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(
        max_length=50,
        choices=[
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia'),
            ('tarjeta', 'Tarjeta')
        ]
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ('completado', 'Completado'),
            ('pendiente', 'Pendiente'),
            ('cancelado', 'Cancelado')
        ],
        default='completado'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'credit_payment'
        verbose_name = 'Pago de Crédito'
        verbose_name_plural = 'Pagos de Crédito'
        ordering = ['-fecha']

    def __str__(self):
        return f"Pago {self.monto_pagado} - {self.metodo}"
