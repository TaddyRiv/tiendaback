from django.contrib import admin

from .models import Category, Provider, Product, ProviderProduct

admin.site.register(Category)
admin.site.register(Provider)
admin.site.register(Product)
admin.site.register(ProviderProduct)
