from rest_framework.routers import DefaultRouter
from creditos.views import CreditInstallmentViewSet

router = DefaultRouter()
router.register(r'cuotas', CreditInstallmentViewSet, basename='creditos-cuotas')

urlpatterns = []
urlpatterns += router.urls
