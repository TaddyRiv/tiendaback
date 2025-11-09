from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .ml_models.predictor_ml import entrenar_modelo, predecir_demanda_rf


class EntrenarModeloMLView(APIView):
    """
    Entrena el modelo de RandomForest con datos históricos de ventas.
    POST -> /api/reportes/ml/entrenar/
    """
    def post(self, request):
        try:
            resultado = entrenar_modelo()
            return Response({
                "mensaje": "Modelo entrenado correctamente ✅",
                "resultados": resultado
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": f"Ocurrió un error al entrenar el modelo: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PredecirDemandaMLView(APIView):
    """
    Genera una predicción de demanda futura para un producto
    GET -> /api/reportes/ml/prediccion/<producto_id>/?dias=30
    """
    def get(self, request, producto_id):
        try:
            dias = int(request.GET.get("dias", 30))
            resultado = predecir_demanda_rf(producto_id, dias)
            return Response({
                "mensaje": "Predicción generada correctamente ✅",
                "prediccion": resultado
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": f"No se pudo generar la predicción: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from .ml_models.recomendador_compras import RecomendadorCompras

class ReporteComprasMLView(APIView):
    """
    Genera un reporte de compras recomendadas basado en predicciones ML.
    GET -> /api/reportes/ml/reporte_compras/
    """
    def get(self, request):
        try:
            solo_necesarios = request.GET.get("solo_necesarios", "true").lower() == "true"
            resultado = RecomendadorCompras.recomendar_todos(solo_necesarios=solo_necesarios)
            return Response({
                "mensaje": "Reporte de compras generado correctamente ✅",
                "fecha": resultado["fecha_analisis"],
                "estadisticas": resultado["estadisticas"],
                "recomendaciones": resultado["recomendaciones"]
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": f"Ocurrió un error al generar el reporte de compras: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
