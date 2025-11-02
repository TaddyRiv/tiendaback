from rest_framework import serializers
from productos.models import Category, Product, Provider, ProviderProduct


# --- Categoría ---
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# --- Proveedor ---
class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = '__all__'


# --- Producto ---
class ProductSerializer(serializers.ModelSerializer):
    categoria = CategorySerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='categoria', write_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'nombre',
            'precio',
            'descripcion',
            'stock',
            'foto',
            'categoria',
            'categoria_id',
        ]

# --- Relación Proveedor - Producto ---
class ProviderProductSerializer(serializers.ModelSerializer):
    proveedor = ProviderSerializer(read_only=True)
    proveedor_id = serializers.PrimaryKeyRelatedField(
        queryset=Provider.objects.all(), source='proveedor', write_only=True
    )

    producto = ProductSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='producto', write_only=True
    )

    class Meta:
        model = ProviderProduct
        fields = ['id', 'proveedor', 'proveedor_id', 'producto', 'producto_id', 'descripcion']
