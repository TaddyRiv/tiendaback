from django.urls import path, include
from rest_framework.routers import DefaultRouter
from productos.views import (
    CategoryViewSet,
    ProviderViewSet,
    ProductViewSet,
    ProviderProductViewSet,
)

router = DefaultRouter()
router.register(r'categorias', CategoryViewSet, basename='categorias')
router.register(r'proveedores', ProviderViewSet, basename='proveedores')
router.register(r'productos', ProductViewSet, basename='productos')
router.register(r'proveedor-producto', ProviderProductViewSet, basename='proveedor-producto')

urlpatterns = [
    path('', include(router.urls)),
]
