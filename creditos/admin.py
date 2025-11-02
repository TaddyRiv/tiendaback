from django.contrib import admin

from .models import CreditConfig, CreditSale, CreditInstallment, CreditPayment

admin.site.register(CreditConfig)
admin.site.register(CreditSale)
admin.site.register(CreditInstallment)
admin.site.register(CreditPayment)
