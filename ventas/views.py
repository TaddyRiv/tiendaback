from rest_framework import viewsets, permissions
from ventas.models import SalesNote, DetailNote, CashPayment
from ventas.serializers import SalesNoteSerializer, DetalleVentaSerializer,MisComprasSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import stripe
from django.conf import settings
from ventas.models import PendingSale
from creditos.models import CreditConfig, CreditPayment
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from productos.models import Product
stripe.api_key = settings.STRIPE_SECRET_KEY
from rest_framework import status
from datetime import timedelta

class SalesNoteViewSet(viewsets.ModelViewSet):
    queryset = SalesNote.objects.all().select_related('cliente', 'empleado')
    serializer_class = SalesNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        # Devolver stock antes de eliminar
        detalles = instance.detalles.all()
        for d in detalles:
            producto = d.producto
            producto.stock += d.cantidad
            producto.save(update_fields=['stock'])
        instance.delete()

class DetailNoteViewSet(viewsets.ModelViewSet):
    queryset = DetailNote.objects.select_related('nota', 'producto').all()
    serializer_class = DetalleVentaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):

        queryset = self.queryset
        nota_id = self.request.query_params.get('nota')
        if nota_id:
            queryset = queryset.filter(nota_id=nota_id)
        return queryset


class CashPaymentViewSet(viewsets.ModelViewSet):
    queryset = CashPayment.objects.select_related('nota').all()
    serializer_class = None  # si más adelante quieres CRUD de pagos contado, define su serializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return Response({"detail": "Endpoint de pagos al contado (CRUD opcional)."})



class StripeCreateIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        print(" DATA RECIBIDA DESDE FRONT:", data)
        tipo_pago = data.get("tipo_pago")
        envio = data.get("envio", {})
        detalles = data.get("detalles", [])
        cliente = data.get("cliente")
        empleado = data.get("empleado")

        if not cliente or not empleado or not detalles:
            return Response({"detail": "Datos incompletos"}, status=400)

        total = Decimal("0.00")
        for d in detalles:
            producto = Product.objects.get(pk=d["producto_id"])
            subtotal = Decimal(producto.precio) * Decimal(d["cantidad"])
            total += subtotal

        total_con_interes = total
        monto_a_cobrar = total

        # 🔹 Calcular interés si es crédito
        if tipo_pago == "credito":
            config = CreditConfig.objects.first()
            if not config:
                return Response({"detail": "Falta configuración de crédito."}, status=400)

            interes = Decimal(config.tasa_interes) / Decimal("100")
            total_con_interes = (total * (1 + interes)).quantize(Decimal("0.01"))
            monto_a_cobrar = (total_con_interes / config.cantidad_cuotas).quantize(Decimal("0.01"))

        # 🔹 Crear PaymentIntent (Stripe simulado)
        intent = stripe.PaymentIntent.create(
            amount=int(monto_a_cobrar * 100),
            currency="usd",
            description=f"Venta tienda - pago {tipo_pago}",
            automatic_payment_methods={"enabled": True},
            metadata={"cliente": str(cliente), "empleado": str(empleado)},
        )

        # 🔹 Guardar venta local (tu flujo actual)
        venta = SalesNote.objects.create(
            cliente_id=cliente,
            empleado_id=empleado,
            tipo_pago=tipo_pago,
            monto=total_con_interes,
            estado="completado" if tipo_pago == "efectivo" else "pendiente",
        )

        for d in detalles:
            producto = Product.objects.get(pk=d["producto_id"])
            DetailNote.objects.create(
                nota=venta,
                producto=producto,
                cantidad=d["cantidad"],
                subtotal=Decimal(producto.precio) * Decimal(d["cantidad"]),
            )

        # 🔹 Si la venta es a crédito → generar el plan de pago automático
        if tipo_pago == "credito":
            try:
                config = CreditConfig.objects.first()
                interes = Decimal(config.tasa_interes) / Decimal("100")
                total_con_interes = (total * (1 + interes)).quantize(Decimal("0.01"))

                from creditos.models import CreditSale, CreditInstallment

                credito = CreditSale.objects.create(
                    nota_venta=venta,
                    total_original=total,
                    total_con_intereses=total_con_interes,
                    tasa_aplicada=config.tasa_interes,
                    saldo_pendiente=total_con_interes,
                    estado="activo",
                    fecha_inicial=timezone.now().date(),
                    fecha_vencimiento=timezone.now().date() + timedelta(
                        days=config.cantidad_cuotas * config.dias_entre_cuotas
                    ),
                )

                monto_cuota = (total_con_interes / Decimal(config.cantidad_cuotas)).quantize(Decimal("0.01"))
                for i in range(1, config.cantidad_cuotas + 1):
                    CreditInstallment.objects.create(
                        venta_credito=credito,
                        numero=i,
                        fecha_vencimiento=timezone.now().date() + timedelta(days=i * config.dias_entre_cuotas),
                        monto=monto_cuota,
                        pagado=False,
                    )

                print(f"✅ Plan de crédito generado: {config.cantidad_cuotas} cuotas de {monto_cuota} Bs.")
            except Exception as e:
                print("❌ Error al crear plan de crédito:", str(e))

        # 🔹 Dirección de envío opcional
        if envio and envio.get("direccion"):
            print("🚚 Dirección registrada:", envio["direccion"])

        print("✅ Venta simulada guardada con ID:", venta.id)

        return Response({"client_secret": intent.client_secret}, status=200)



@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = []

    def post(self, request):
        payload = request.body
        sig = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(

                payload=payload,
                sig_header=sig,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
            print(" WEBHOOK RECIBIDO:", event["type"])

        except Exception as e:
            return Response({"error": str(e)}, status=400)

        if event["type"] == "payment_intent.succeeded":
            intent = event["data"]["object"]
            intent_id = intent["id"]

            try:
                with transaction.atomic():
                    pend = PendingSale.objects.select_for_update().get(intent_id=intent_id, estado="pendiente")

                    payload_venta = {
                        "cliente": pend.cliente_id,
                        "empleado": pend.empleado_id,
                        "monto": str(pend.monto),
                        "tipo_pago": pend.tipo_pago,
                        "detalles": pend.detalles,
                    }

                    # Crear venta real con tu serializer
                    serializer = SalesNoteSerializer(data=payload_venta)
                    serializer.is_valid(raise_exception=True)
                    nota = serializer.save()

                    # Si es crédito → marcar primera cuota como pagada
                    if pend.tipo_pago == "credito":
                        credito = nota.creditos.first()
                        if credito:
                            primera = credito.cuotas.first()
                            if primera:
                                primera.pagado = True
                                primera.fecha_pago = timezone.now().date()
                                primera.save()

                                CreditPayment.objects.create(
                                    cuota=primera,
                                    monto_pagado=primera.monto,
                                    metodo="tarjeta",
                                    estado="completado",
                                )

                    pend.estado = "creada"
                    pend.save(update_fields=["estado"])

            except PendingSale.DoesNotExist:
                pass  # Ya procesado

        return Response({"status": "ok"}, status=200)
    
class MisComprasView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        ventas = (
            SalesNote.objects
            .filter(cliente=user)
            .select_related("empleado")
            .prefetch_related("detalles__producto")
            .order_by("-fecha")
        )

        serializer = MisComprasSerializer(ventas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
