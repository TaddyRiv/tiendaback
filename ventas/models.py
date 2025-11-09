from django.db import models
from usuarios.models import Usuario
from productos.models import Product
from django.utils import timezone
class SalesNote(models.Model):
    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='ventas_como_cliente'
    )
    empleado = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ventas_realizadas'
    )
    fecha = models.DateField(default=timezone.now)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_pago = models.CharField(max_length=50)
    estado = models.CharField(max_length=20, default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sales_note'
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente.email}"



class DetailNote(models.Model):
    nota = models.ForeignKey(SalesNote, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Product, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'detail_note'

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"



class CashPayment(models.Model):
    nota = models.ForeignKey(SalesNote, on_delete=models.CASCADE, related_name='pagos')
    fecha = models.DateField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=50, choices=[
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta')
    ])
    estado = models.CharField(max_length=20, default='completado')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cash_payment'

    def __str__(self):
        return f"Pago {self.metodo} - {self.monto}"
    

class PendingSale(models.Model):
    intent_id = models.CharField(max_length=100, unique=True)
    cliente_id = models.IntegerField()
    empleado_id = models.IntegerField()
    tipo_pago = models.CharField(max_length=20)  # "efectivo" | "tarjeta" | "credito"
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    detalles = models.JSONField()  # [{producto_id, cantidad, subtotal}, ...]
    estado = models.CharField(
        max_length=20,
        choices=[('pendiente', 'Pendiente'), ('creada', 'Creada'), ('fallida', 'Fallida')],
        default='pendiente'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pending_sale'
        verbose_name = 'Venta Pendiente'
        verbose_name_plural = 'Ventas Pendientes'
        ordering = ['-created_at']

    def __str__(self):
        return f"PendingSale #{self.id} - {self.tipo_pago} ({self.estado})"