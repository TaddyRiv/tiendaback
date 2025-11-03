from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.permissions import AllowAny

from productos.models import Category, Product, Provider, ProviderProduct
from productos.serializers import (
    CategorySerializer,
    ProductSerializer,
    ProviderSerializer,
    ProviderProductSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('descripcion')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.all().order_by('nombre')
    serializer_class = ProviderSerializer
    permission_classes = [IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('categoria')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    # --- NUEVA ACCIÓN PERSONALIZADA ---
    @action(detail=True, methods=['post'], url_path='ajustar_stock')
    def ajustar_stock(self, request, pk=None):
        try:
            producto = self.get_object()
            accion = request.data.get("accion")
            cantidad = int(request.data.get("cantidad", 0))

            if cantidad <= 0:
                return Response(
                    {"error": "La cantidad debe ser mayor a 0."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if accion == "sumar":
                producto.stock += cantidad
            elif accion == "restar":
                if producto.stock < cantidad:
                    return Response(
                        {"error": f"Stock insuficiente. Disponible: {producto.stock}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                producto.stock -= cantidad
            else:
                return Response(
                    {"error": "Acción inválida. Use 'sumar' o 'restar'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            producto.save(update_fields=['stock'])

            return Response({
                "mensaje": f"Stock actualizado correctamente.",
                "producto": producto.nombre,
                "nuevo_stock": producto.stock
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProviderProductViewSet(viewsets.ModelViewSet):
    queryset = ProviderProduct.objects.select_related('proveedor', 'producto').all()
    serializer_class = ProviderProductSerializer
    permission_classes = [IsAuthenticated]
