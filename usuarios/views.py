from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from usuarios.models import Usuario
from usuarios.serializers import UsuarioSerializer, LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from usuarios.models import Rol
from usuarios.serializers import RolSerializer
from django.db.models import ProtectedError
from rest_framework.decorators import action

# --- Login ---
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UsuarioSerializer(user).data
        })


# --- CRUD de usuarios ---
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.estado = False  # Desactivar en lugar de eliminar
        instance.save()
        return Response(
            {"detail": "Usuario desactivado correctamente."},
            status=status.HTTP_200_OK
        )
    @action(detail=False, methods=['get'])
    def empleados(self, request):
        empleados = Usuario.objects.filter(rol__nombre__iexact="Empleado", estado=True)
        serializer = self.get_serializer(empleados, many=True)
        return Response(serializer.data)

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]