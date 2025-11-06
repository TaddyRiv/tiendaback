# productos/serializers.py
from rest_framework import serializers
from productos.models import Category, Product, Provider, ProviderProduct

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    categoria = CategorySerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='categoria', write_only=True
    )
    # 👉 devolvemos URL absoluta
   # foto = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'nombre',
            'precio',
            'descripcion',
            'stock',
            'foto',              # ahora es la URL absoluta o None
            'categoria',
            'categoria_id',
        ]

    # def get_foto(self, obj):
    #     if not obj.foto:
    #         return None
    #     request = self.context.get('request')
    #     url = obj.foto.url  # p.ej. /media/productos/...
    #     return request.build_absolute_uri(url) if request else url

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
