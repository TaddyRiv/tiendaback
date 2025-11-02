import random
import string
from decimal import Decimal
from datetime import date, timedelta, datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from usuarios.models import Usuario, Rol
from productos.models import Product, Category, Provider, ProviderProduct
from ventas.models import SalesNote, DetailNote, CashPayment
from creditos.models import CreditConfig, CreditSale, CreditInstallment, CreditPayment


class Command(BaseCommand):
    help = "Genera usuarios masivos, productos, ventas al contado y a crédito distribuidas en 6 meses"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🚀 Iniciando seeder masivo de ventas y créditos..."))
        self.create_massive_users()
        self.create_products_if_needed()
        self.create_sales_data()
        self.stdout.write(self.style.SUCCESS("✅ Seeder masivo completado exitosamente."))

    # --------------------------------------------------------
    # 1️⃣ Crear usuarios masivos
    # --------------------------------------------------------
    def create_massive_users(self):
        cliente_rol = Rol.objects.filter(nombre="Cliente").first()
        empleado_rol = Rol.objects.filter(nombre="Empleado").first()

        # Crear 80 clientes
        for i in range(1, 81):
            email = f"cliente{i}@tienda.com"
            Usuario.objects.get_or_create(
                email=email,
                defaults={
                    "username": f"cliente{i}",
                    "first_name": f"Cliente {i}",
                    "password": "123",
                    "rol": cliente_rol,
                },
            )

        # Crear 6 empleados
        for i in range(1, 7):
            email = f"empleado{i}@tienda.com"
            Usuario.objects.get_or_create(
                email=email,
                defaults={
                    "username": f"empleado{i}",
                    "first_name": f"Empleado {i}",
                    "password": "123",
                    "rol": empleado_rol,
                    "is_staff": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("👥 80 clientes y 6 empleados creados correctamente."))

    # --------------------------------------------------------
    # 2️⃣ Crear productos (si faltan)
    # --------------------------------------------------------
    def create_products_if_needed(self):
        if Product.objects.count() >= 30:
            self.stdout.write(self.style.NOTICE("📦 Ya existen productos suficientes."))
            return

        categorias = ["Ropa", "Calzado", "Tecnología", "Hogar", "Electrodomésticos"]
        for c in categorias:
            Category.objects.get_or_create(descripcion=c)

        proveedores = ["Proveedor A", "Proveedor B", "Proveedor C", "Proveedor D"]
        for p in proveedores:
            Provider.objects.get_or_create(nombre=p, telefono=f"7{random.randint(1000000,9999999)}")

        for i in range(1, 31):
            categoria = random.choice(Category.objects.all())
            producto, _ = Product.objects.get_or_create(
                nombre=f"Producto {i}",
                defaults={
                    "precio": Decimal(random.randint(20, 500)),
                    "descripcion": f"Producto de ejemplo {i}",
                    "stock": random.randint(20, 150),
                    "categoria": categoria,
                },
            )
            for proveedor in Provider.objects.all():
                ProviderProduct.objects.get_or_create(
                    proveedor=proveedor,
                    producto=producto,
                    defaults={"precio_compra": producto.precio * Decimal("0.6")},
                )

        self.stdout.write(self.style.SUCCESS("🛒 Productos y proveedores creados."))

    # --------------------------------------------------------
    # 3️⃣ Crear ventas distribuidas desde mayo a hoy
    # --------------------------------------------------------
    def create_sales_data(self):
        empleados = list(Usuario.objects.filter(rol__nombre="Empleado"))
        clientes = list(Usuario.objects.filter(rol__nombre="Cliente"))
        productos = list(Product.objects.all())

        fecha_inicio = date(date.today().year, 5, 1)
        fecha_fin = date.today()
        dias_totales = (fecha_fin - fecha_inicio).days

        config, _ = CreditConfig.objects.get_or_create(
            monto_max=Decimal("500.00"),
            tasa_interes=Decimal("10.00"),
            cantidad_cuotas=3,
            dias_entre_cuotas=10,
        )

        total_ventas = 0
        total_creditos = 0

        for cliente in clientes:
            num_ventas = random.randint(2, 6)  # 2-6 ventas por cliente
            for _ in range(num_ventas):
                fecha_venta = fecha_inicio + timedelta(days=random.randint(0, dias_totales))
                empleado = random.choice(empleados)
                tipo = random.choice(["contado", "credito", "credito", "credito"])  # más probabilidad de crédito

                nota = SalesNote.objects.create(
                    cliente=cliente,
                    empleado=empleado,
                    monto=0,
                    tipo_pago=tipo,
                    estado="completado" if tipo == "contado" else "pendiente",
                    fecha=fecha_venta,
                )

                total = Decimal("0.00")
                for _ in range(random.randint(1, 4)):  # productos por venta
                    producto = random.choice(productos)
                    cantidad = random.randint(1, 5)
                    subtotal = producto.precio * cantidad
                    DetailNote.objects.create(
                        nota=nota,
                        producto=producto,
                        cantidad=cantidad,
                        subtotal=subtotal,
                        fecha=fecha_venta,
                    )
                    total += subtotal

                nota.monto = total
                nota.save()
                total_ventas += 1

                if tipo == "contado":
                    CashPayment.objects.create(
                        nota=nota,
                        monto=total,
                        metodo=random.choice(["efectivo", "tarjeta", "transferencia"]),
                        fecha=fecha_venta,
                    )
                else:
                # ✅ Verificar si el monto es menor o igual al límite de crédito
                    if total <= config.monto_max:
                        total_creditos += 1
                        self.create_credit_sale(nota, total, config, fecha_venta)
                    else:
                    # ⚠️ Si excede el límite, convertir la venta a contado automáticamente
                        nota.tipo_pago = "contado"
                        nota.estado = "completado"
                        nota.save()
                        CashPayment.objects.create(
                            nota=nota,
                            monto=total,
                            metodo=random.choice(["efectivo", "tarjeta", "transferencia"]),
                            fecha=fecha_venta,
                        )

        self.stdout.write(
            self.style.SUCCESS(
            f"💰 Ventas generadas: {total_ventas} (de las cuales {total_creditos} fueron a crédito)"
            )
    )


    # --------------------------------------------------------
    # 4️⃣ Crear ventas a crédito y cuotas
    # --------------------------------------------------------
    def create_credit_sale(self, nota, total, config, fecha_inicial):
        interes = total * (config.tasa_interes / 100)
        total_con_interes = total + interes
        estado_credito = random.choice(["activo", "pagado", "atrasado"])

        credito = CreditSale.objects.create(
            nota_venta=nota,
            total_original=total,
            total_con_intereses=total_con_interes,
            tasa_aplicada=config.tasa_interes,
            saldo_pendiente=total_con_interes if estado_credito != "pagado" else Decimal("0.00"),
            estado=estado_credito,
            fecha_inicial=fecha_inicial,
            fecha_vencimiento=fecha_inicial
            + timedelta(days=config.cantidad_cuotas * config.dias_entre_cuotas),
        )

        monto_cuota = round(total_con_interes / config.cantidad_cuotas, 2)

        for i in range(1, config.cantidad_cuotas + 1):
            fecha_v = fecha_inicial + timedelta(days=i * config.dias_entre_cuotas)
            cuota = CreditInstallment.objects.create(
                venta_credito=credito,
                numero=i,
                cuota=f"Cuota {i}",
                fecha_vencimiento=fecha_v,
                monto=monto_cuota,
                pagado=(estado_credito == "pagado" and i <= random.randint(1, 3)),
                fecha_pago=fecha_v if estado_credito == "pagado" else None,
            )

            # Generar algunos pagos
            if cuota.pagado:
                CreditPayment.objects.create(
                    cuota=cuota,
                    monto_pagado=monto_cuota,
                    metodo=random.choice(["efectivo", "tarjeta", "transferencia"]),
                    fecha=fecha_v,
                )
