# tienda/management/commands/seed_tienda.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import random
from datetime import date, timedelta

from faker import Faker

from usuarios.models import Usuario, Rol
from productos.models import Category, Provider, Product, ProviderProduct
from ventas.models import SalesNote, DetailNote, CashPayment
from creditos.models import CreditConfig, CreditSale, CreditInstallment, CreditPayment


class Command(BaseCommand):
    help = "Puebla la base con clientes, proveedores, categorías, productos y ventas (contado/crédito) del último año."

    def add_arguments(self, parser):
        parser.add_argument("--clientes", type=int, default=50, help="Cantidad de clientes a crear (por defecto 50)")
        parser.add_argument("--ventas", type=int, default=1500, help="Cantidad total de ventas a generar (aprox.)")

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker("es_ES")
        random.seed(2025)

        cant_clientes = int(options["clientes"])
        ventas_objetivo = int(options["ventas"])

        self.stdout.write(self.style.MIGRATE_HEADING("==> Iniciando seeding de tienda..."))

        # 1) Empleados disponibles (usaremos el empleado existente y/o admins como fallback)
        empleados = list(Usuario.objects.filter(rol__nombre__in=["Empleado", "Admin", "SuperAdmin"], is_active=True))
        if not empleados:
            # Fallback: cualquier usuario activo
            empleados = list(Usuario.objects.filter(is_active=True))
        if not empleados:
            raise SystemExit("No hay usuarios/empleados disponibles. Ejecuta primero tu seeder de roles/usuarios.")

        # 2) Crear clientes (solo añadir, no borrar)
        clientes_nuevos = self._crear_clientes(fake, cant_clientes)
        self.stdout.write(self.style.SUCCESS(f"✓ Clientes creados: {len(clientes_nuevos)}"))

        # 3) Proveedores
        proveedores = self._crear_proveedores(fake)
        self.stdout.write(self.style.SUCCESS(f"✓ Proveedores creados/obtenidos: {len(proveedores)}"))

        # 4) Categorías y productos (15–20 por categoría)
        categorias, productos = self._crear_categorias_y_productos(fake, proveedores)
        self.stdout.write(self.style.SUCCESS(f"✓ Categorías: {len(categorias)} | Productos nuevos: {len(productos)}"))

        # 5) Configuración de crédito
        config_credito = self._get_or_create_credit_config()
        self.stdout.write(self.style.SUCCESS("✓ CreditConfig listo"))

        # 6) Generar ventas entre nov/2024 y nov/2025
        fecha_inicio = date(2024, 11, 1)
        fecha_fin = date(2025, 11, 8)  # hoy según tu contexto; ajusta si prefieres 30/11/2025

        ventas_creadas = self._generar_ventas(
            fake=fake,
            empleados=empleados,
            clientes=clientes_nuevos,
            productos=productos,
            config=config_credito,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            ventas_objetivo=ventas_objetivo,
            propor_credito=0.30,  # 30% crédito
        )
        self.stdout.write(self.style.SUCCESS(f"✓ Ventas creadas: {ventas_creadas}"))

        # 7) Actualizar métricas de clientes
        self._refrescar_metricas_clientes()
        self.stdout.write(self.style.SUCCESS("✓ Métricas de clientes actualizadas"))

        self.stdout.write(self.style.SUCCESS("🎉 Seeding finalizado con éxito."))

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _crear_clientes(self, fake: Faker, cantidad: int):
        clientes = []
        try:
            rol_cliente = Rol.objects.get(nombre="Cliente")
        except Rol.DoesNotExist:
            rol_cliente = None

        existentes_emails = set(Usuario.objects.values_list("email", flat=True))

        for _ in range(cantidad):
            # Evitar duplicados por email
            for _retry in range(5):
                nombre = fake.first_name()
                apellido = fake.last_name()
                email = f"{nombre}.{apellido}{random.randint(1,9999)}@mail.com".lower()
                if email not in existentes_emails:
                    existentes_emails.add(email)
                    break

            estado_credito = random.choices(
                population=["activo", "solo_contado", "bloqueado"],
                weights=[0.75, 0.2, 0.05],
                k=1
            )[0]

            clientes.append(
                Usuario(
                    username=f"{nombre}_{apellido}".lower()[:150],
                    email=email,
                    telefono=fake.phone_number()[:20],
                    direccion=fake.address()[:200],
                    estado_credito=estado_credito,
                    is_active=True,
                    rol=rol_cliente
                )
            )

        # bulk_create omite set_password, pero no usaremos login de estos clientes ficticios.
        Usuario.objects.bulk_create(clientes, ignore_conflicts=True)
        # Devolver queryset de los recién creados
        creados = list(Usuario.objects.filter(email__in=[c.email for c in clientes]))
        return creados

    def _crear_proveedores(self, fake: Faker):
        nombres = [
            "Textiles Andinos SRL", "Moda y Estilo SA", "Calzados Rivera",
            "Sombreros del Sur", "Abrigos del Altiplano", "Denim Factory",
            "Urban Sneakers Bolivia", "Elegancia & Co.", "Gabardinas Premium",
        ]
        proveedores = []
        for nom in nombres:
            prov, _ = Provider.objects.get_or_create(
                nombre=nom,
                defaults={"telefono": fake.phone_number()[:20]}
            )
            proveedores.append(prov)
        return proveedores

    def _crear_categorias_y_productos(self, fake: Faker, proveedores):
        categorias_def = [
            ("Camisas", (70, 180)),
            ("Pantalones", (90, 250)),
            ("Shorts", (60, 150)),
            ("Vestidos", (120, 400)),
            ("Abrigos", (200, 650)),
            ("Sombreros", (50, 180)),
            ("Calzados", (180, 550)),
            ("Sandalias", (80, 220)),
            ("Tenis", (220, 700)),
            ("Gabardinas", (180, 500)),
            ("Chaquetas", (160, 480)),
        ]
        categorias = []
        productos_nuevos = []

        adjetivos = ["algodón", "lino", "mezclilla", "impermeable", "deportiva", "casual", "clásica", "premium"]
        colores = ["negro", "blanco", "azul", "rojo", "verde", "gris", "beige", "marrón"]
        tallas_ropa = ["XS", "S", "M", "L", "XL"]
        tallas_calzado = [str(x) for x in range(36, 45)]

        for nombre_cat, (pmin, pmax) in categorias_def:
            cat, _ = Category.objects.get_or_create(descripcion=nombre_cat)
            categorias.append(cat)

            cantidad = random.randint(15, 20)
            for _ in range(cantidad):
                if nombre_cat in ["Calzados", "Sandalias", "Tenis"]:
                    talla = random.choice(tallas_calzado)
                    nombre = f"{nombre_cat[:-1] if nombre_cat.endswith('s') else nombre_cat} {random.choice(adjetivos)} {random.choice(colores)} T{talla}"
                else:
                    talla = random.choice(tallas_ropa)
                    nombre = f"{nombre_cat[:-1] if nombre_cat.endswith('s') else nombre_cat} {random.choice(adjetivos)} {random.choice(colores)} T{talla}"

                precio = Decimal(random.randint(pmin, pmax))
                stock = random.randint(20, 200)
                prod, creado = Product.objects.get_or_create(
                    nombre=nombre[:100],
                    categoria=cat,
                    defaults={
                        "precio": precio,
                        "descripcion": fake.sentence(nb_words=8),
                        "stock": stock,
                    }
                )
                if creado:
                    productos_nuevos.append(prod)

                # Vincular 1–2 proveedores con precio de compra
                for prov in random.sample(proveedores, k=random.choice([1, 1, 2])):
                    ProviderProduct.objects.get_or_create(
                        proveedor=prov,
                        producto=prod,
                        defaults={
                            "precio_compra": (precio * Decimal("0.6")).quantize(Decimal("1.00")),
                            "descripcion": f"Compra a {prov.nombre}"
                        }
                    )

        return categorias, productos_nuevos

    def _get_or_create_credit_config(self):
        config, _ = CreditConfig.objects.get_or_create(
            monto_max=Decimal("1500.00"),
            tasa_interes=Decimal("10.00"),
            cantidad_cuotas=3,
            dias_entre_cuotas=15,
        )
        return config

    def _generar_ventas(
        self, fake: Faker, empleados, clientes, productos, config,
        fecha_inicio: date, fecha_fin: date, ventas_objetivo: int, propor_credito: float = 0.30
    ):
        # Distribución por meses (más ventas en dic, mar, ago)
        pesos_mes = {
            1: 0.8,  2: 0.9,  3: 1.2,  4: 1.0,  5: 1.0,  6: 1.1,
            7: 1.0,  8: 1.2,  9: 1.0, 10: 1.0, 11: 1.0, 12: 1.4
        }

        dias_total = (fecha_fin - fecha_inicio).days + 1
        if dias_total <= 0:
            return 0

        ventas_creadas = 0
        for i in range(dias_total):
            fecha = fecha_inicio + timedelta(days=i)
            # Calcular ventas por día en base al peso del mes (redondeo mínimo 0–6 aprox.)
            base_diaria = ventas_objetivo / dias_total
            factor = pesos_mes.get(fecha.month, 1.0)
            estimado = base_diaria * factor
            ventas_dia = max(0, int(random.gauss(mu=estimado, sigma=max(1.0, estimado * 0.35))))
            ventas_dia = min(ventas_dia, 12)  # techo para no explotar

            for _ in range(ventas_dia):
                empleado = random.choice(empleados)
                cliente = random.choice(clientes)

                # Si el cliente está bloqueado no compra
                if cliente.estado_credito == "bloqueado":
                    continue

                # Carrito 1–5 items
                items = random.sample(productos, k=random.randint(1, min(5, len(productos))))
                cantidades = [random.randint(1, 3) for _ in items]

                # Calcular monto
                total = Decimal("0.00")
                for prod, cant in zip(items, cantidades):
                    total += (prod.precio * Decimal(cant))

                # Tipo de pago
                es_credito = random.random() < propor_credito and cliente.estado_credito == "activo" and total <= config.monto_max
                tipo_pago = "credito" if es_credito else random.choice(["efectivo", "tarjeta", "transferencia"])

                # Crear SalesNote con fecha específica (auto_now_add permite asignar manualmente al crear)
                nota = SalesNote.objects.create(
                    cliente=cliente,
                    empleado=empleado,
                    fecha=fecha,            # <- asignación explícita OK
                    monto=total.quantize(Decimal("1.00")),
                    tipo_pago=tipo_pago,
                    estado="completado" if not es_credito else "pendiente"
                )

                # Detalles + ajustar stock
                for prod, cant in zip(items, cantidades):
                    subtotal = (prod.precio * Decimal(cant)).quantize(Decimal("1.00"))
                    DetailNote.objects.create(
                        nota=nota,
                        producto=prod,
                        fecha=fecha,
                        cantidad=cant,
                        subtotal=subtotal
                    )
                    # bajar stock (sin ir negativo)
                    Product.objects.filter(pk=prod.pk).update(stock=max(0, prod.stock - cant))

                if es_credito:
                    self._crear_credito(nota, fecha, config, total)
                else:
                    # Pago al contado
                    CashPayment.objects.create(
                        nota=nota,
                        fecha=fecha,
                        monto=nota.monto,
                        metodo=tipo_pago if tipo_pago in ("efectivo", "transferencia", "tarjeta") else "efectivo",
                        estado="completado"
                    )
                    nota.estado = "completado"
                    nota.save(update_fields=["estado"])

                ventas_creadas += 1

        return ventas_creadas

    def _crear_credito(self, nota: SalesNote, fecha_inicial: date, config: CreditConfig, total_original: Decimal):
        # Interés simple sobre total
        tasa = (config.tasa_interes / Decimal("100.00"))
        total_con_interes = (total_original * (Decimal("1.00") + tasa)).quantize(Decimal("1.00"))

        # Crear CreditSale
        dias_total = config.cantidad_cuotas * config.dias_entre_cuotas
        fecha_venc = fecha_inicial + timedelta(days=dias_total)

        credito = CreditSale.objects.create(
            nota_venta=nota,
            total_original=total_original.quantize(Decimal("1.00")),
            total_con_intereses=total_con_interes,
            tasa_aplicada=config.tasa_interes,
            saldo_pendiente=total_con_interes,
            estado="activo",
            fecha_inicial=fecha_inicial,
            fecha_vencimiento=fecha_venc
        )

        # Crear cuotas iguales
        monto_cuota = (total_con_interes / Decimal(config.cantidad_cuotas)).quantize(Decimal("1.00"))
        saldo = total_con_interes
        for n in range(1, config.cantidad_cuotas + 1):
            fv = fecha_inicial + timedelta(days=config.dias_entre_cuotas * n)
            # nombre de la cuota (ej. "1/3")
            cuota = CreditInstallment.objects.create(
                venta_credito=credito,
                numero=n,
                cuota=f"{n}/{config.cantidad_cuotas}",
                fecha_vencimiento=fv,
                monto=monto_cuota,
                pagado=False
            )

            # Simular pagos: ~75% pagan a tiempo, 15% con retraso, 10% impagos
            r = random.random()
            if r < 0.75:
                # paga antes o en fecha
                fp = fv - timedelta(days=random.randint(0, 3))
                CreditPayment.objects.create(
                    cuota=cuota,
                    fecha=fp,
                    monto_pagado=monto_cuota,
                    metodo=random.choice(["efectivo", "transferencia", "tarjeta"]),
                    estado="completado"
                )
                cuota.pagado = True
                cuota.fecha_pago = fp
                cuota.save(update_fields=["pagado", "fecha_pago"])
                saldo -= monto_cuota
            elif r < 0.90:
                # paga con retraso
                fp = fv + timedelta(days=random.randint(1, 20))
                CreditPayment.objects.create(
                    cuota=cuota,
                    fecha=fp,
                    monto_pagado=monto_cuota,
                    metodo=random.choice(["efectivo", "transferencia", "tarjeta"]),
                    estado="completado"
                )
                cuota.pagado = True
                cuota.fecha_pago = fp
                cuota.save(update_fields=["pagado", "fecha_pago"])
                saldo -= monto_cuota
            else:
                # impago: queda pendiente
                pass

        # Actualizar saldo/estado del crédito
        credito.saldo_pendiente = max(Decimal("0.00"), saldo).quantize(Decimal("1.00"))
        if credito.saldo_pendiente <= 0:
            credito.estado = "pagado"
            nota.estado = "completado"
            nota.save(update_fields=["estado"])
        else:
            # Si tiene alguna cuota vencida y no pagada, marcar atrasado
            hay_vencidas_impagas = credito.cuotas.filter(
                pagado=False, fecha_vencimiento__lt=timezone.now().date()
            ).exists()
            if hay_vencidas_impagas:
                credito.estado = "atrasado"
        credito.save(update_fields=["saldo_pendiente", "estado"])

    def _refrescar_metricas_clientes(self):
        # Recalcular compras_realizadas y total_gastado
        for u in Usuario.objects.all():
            ventas = SalesNote.objects.filter(cliente=u)
            total = Decimal("0.00")
            count = ventas.count()
            for v in ventas:
                total += v.monto
            u.compras_realizadas = count
            u.total_gastado = total.quantize(Decimal("1.00"))
            # Si tiene créditos atrasados, puede bloquearse (pequeña regla opcional)
            atrasados = False
            for v in ventas:
                if hasattr(v, "creditos"):
                    if v.creditos.filter(estado="atrasado").exists():
                        atrasados = True
                        break
            if atrasados and u.estado_credito == "activo" and random.random() < 0.2:
                u.estado_credito = "solo_contado"
            u.save(update_fields=["compras_realizadas", "total_gastado", "estado_credito"])
