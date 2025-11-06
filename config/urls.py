from django.contrib import admin
from django.urls import path
from django.urls import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('usuarios.urls')),
    path('api/', include('productos.urls')),
    path('api/', include('ventas.urls')),
    path('api/reportes/', include('reportes.urls')),
]
