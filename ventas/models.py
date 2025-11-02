from django.db import models
from usuarios.models import Usuario
from productos.models import Product

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
    fecha = models.DateField(auto_now_add=True)
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