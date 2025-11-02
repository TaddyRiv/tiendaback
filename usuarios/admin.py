from django.contrib import admin
from .models import Usuario, Rol, Permiso, RolPermiso

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "rol", "estado_credito", "estado")

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre", "estado")
   # filter_horizontal = ("permisos",)

@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "modulo", "estado")

@admin.register(RolPermiso)
class RolPermisoAdmin(admin.ModelAdmin):
    list_display = ("rol", "permiso", "estado")
