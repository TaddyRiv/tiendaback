from django.db import models
from usuarios.models import Usuario

class HistorialReporte(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="reportes_generados")
    tipo = models.CharField(max_length=150)
    parametros = models.JSONField(default=dict)
    resultado_resumen = models.TextField(blank=True, null=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historial_reporte"
        ordering = ["-fecha_generacion"]

    def __str__(self):
        return f"{self.tipo} - {self.usuario.email} ({self.fecha_generacion:%Y-%m-%d %H:%M})"
