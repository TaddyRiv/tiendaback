from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from usuarios.models import Rol, Usuario, Permiso

class Command(BaseCommand):
    help = "Crea los roles base, permisos y usuarios iniciales"

    def handle(self, *args, **options):

        permisos_data = [
            # --- Usuarios ---
            ("ver_usuarios", "Puede ver la lista de usuarios", "Usuarios"),
            ("crear_usuarios", "Puede crear nuevos usuarios", "Usuarios"),
            ("editar_usuarios", "Puede editar usuarios existentes", "Usuarios"),
            ("eliminar_usuarios", "Puede eliminar usuarios", "Usuarios"),

            # --- Productos ---
            ("ver_productos", "Puede ver productos", "Productos"),
            ("crear_productos", "Puede crear productos", "Productos"),
            ("editar_productos", "Puede editar productos", "Productos"),
            ("eliminar_productos", "Puede eliminar productos", "Productos"),

            # --- Ventas ---
            ("ver_ventas", "Puede ver las ventas", "Ventas"),
            ("crear_ventas", "Puede registrar nuevas ventas", "Ventas"),
            ("editar_ventas", "Puede editar ventas", "Ventas"),
            ("eliminar_ventas", "Puede eliminar ventas", "Ventas"),

            # --- Créditos ---
            ("ver_creditos", "Puede ver créditos", "Créditos"),
            ("crear_creditos", "Puede crear créditos", "Créditos"),
            ("editar_creditos", "Puede modificar créditos", "Créditos"),

            # --- Reportes ---
            ("ver_reportes", "Puede ver reportes", "Reportes"),

            # --- Cliente ---
            ("ver_tienda", "Puede ver productos y realizar compras", "Tienda"),
            ("realizar_compra", "Puede realizar compras", "Tienda"),
        ]

        for nombre, descripcion, modulo in permisos_data:
            Permiso.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion, 'modulo': modulo}
            )

        self.stdout.write(self.style.SUCCESS("Permisos creados correctamente."))

        #crear roles
        roles = {
            "SuperAdmin": "Control total del sistema.",
            "Admin": "Gestión de usuarios, ventas y productos.",
            "Empleado": "Gestión limitada a ventas e inventario.",
            "Cliente": "Solo puede ver y comprar productos.",
        }

        for nombre, desc in roles.items():
            Rol.objects.get_or_create(nombre=nombre, defaults={'descripcion': desc})

        self.stdout.write(self.style.SUCCESS("Roles base creados."))

        # asignar permisos a roles
        superadmin = Rol.objects.get(nombre="SuperAdmin")
        admin = Rol.objects.get(nombre="Admin")
        empleado = Rol.objects.get(nombre="Empleado")
        cliente = Rol.objects.get(nombre="Cliente")

        # Asignaciones
        superadmin.permisos.set(Permiso.objects.all())

        admin.permisos.set(Permiso.objects.filter(
            modulo__in=["Usuarios", "Productos", "Ventas", "Créditos", "Reportes"]
        ))

        empleado.permisos.set(Permiso.objects.filter(
            modulo__in=["Productos", "Ventas"]
        ))

        cliente.permisos.set(Permiso.objects.filter(
            modulo__in=["Tienda"]
        ))

        self.stdout.write(self.style.SUCCESS("Permisos asignados por rol correctamente."))

        usuarios_data = [
            ("superadmin", "admin@admin.com", "123", superadmin),
            ("admin", "admin@tienda.com", "123", admin),
            ("empleado", "empleado@tienda.com", "123", empleado),
            ("cliente", "cliente@tienda.com", "123", cliente),
        ]

        for username, email, password, rol in usuarios_data:
            if not Usuario.objects.filter(email=email).exists():
                Usuario.objects.create(
                    username=username,
                    email=email,
                    password=make_password(password),
                    rol=rol,
                    is_staff=(rol.nombre in ["SuperAdmin", "Admin"]),
                    is_superuser=(rol.nombre == "SuperAdmin")
                )

        self.stdout.write(self.style.SUCCESS("Usuarios base creados correctamente."))
