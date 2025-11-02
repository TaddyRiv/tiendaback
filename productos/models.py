from django.db import models

class Category(models.Model):
    descripcion = models.CharField(max_length=100)

    class Meta:
        db_table = 'category'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['descripcion']

    def __str__(self):
        return self.descripcion


class Provider(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'provider'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Product(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    stock = models.IntegerField(default=0)
    foto = models.ImageField(upload_to='productos/', blank=True, null=True)
    categoria = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='productos')

    proveedores = models.ManyToManyField(
        Provider,
        through='ProviderProduct',
        related_name='productos'
    )

    class Meta:
        db_table = 'product'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class ProviderProduct(models.Model):
    proveedor = models.ForeignKey(Provider, on_delete=models.CASCADE)
    producto = models.ForeignKey(Product, on_delete=models.CASCADE) 
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    descripcion = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'provider_product'
        verbose_name = 'Producto de Proveedor'
        verbose_name_plural = 'Productos de Proveedores'
        unique_together = ('proveedor', 'producto')

    def __str__(self):
        return f"{self.proveedor.nombre} - {self.producto.nombre}"