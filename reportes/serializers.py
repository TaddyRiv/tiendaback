from rest_framework import serializers
from .models import HistorialReporte

class HistorialReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialReporte
        fields = "__all__"
