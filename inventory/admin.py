from django.contrib import admin
from .models import Product, Sale, StockAlert

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'current_stock', 'low_stock_threshold', 'is_low_stock']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'sku']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'date', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['product__name']

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'alert_type', 'is_active', 'created_at']
    list_filter = ['alert_type', 'is_active', 'created_at']
    search_fields = ['product__name']