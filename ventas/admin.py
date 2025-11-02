from django.contrib import admin

from .models import SalesNote,DetailNote,CashPayment   



admin.site.register(SalesNote)
admin.site.register(DetailNote)
admin.site.register(CashPayment)

