from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios.views import UsuarioViewSet, LoginView
from usuarios.views import RolViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')
router.register(r'roles', RolViewSet, basename='roles') 
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
]
