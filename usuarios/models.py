from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# --- Permisos ---
class Permiso(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    modulo = models.CharField(max_length=50, blank=True)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "permiso"


# --- Roles ---
class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    permisos = models.ManyToManyField(Permiso, through='RolPermiso', related_name='roles')
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "rol"


# --- Relación intermedia entre roles y permisos ---
class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rol_permiso"
        unique_together = ('rol', 'permiso')


# --- Usuario ---
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    
class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    estado_credito = models.CharField(
        max_length=20,
        choices=[('activo', 'Activo'), ('solo_contado', 'Solo contado'), ('bloqueado', 'Bloqueado')],
        default='activo'
    )
    compras_realizadas = models.PositiveIntegerField(default=0)
    total_gastado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_bloqueo = models.DateField(null=True, blank=True)
    estado = models.BooleanField(default=True)
    rol = models.ForeignKey('Rol', on_delete=models.SET_NULL, null=True, blank=True)

    USERNAME_FIELD = 'email'       
    REQUIRED_FIELDS = []          

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = "usuario"

