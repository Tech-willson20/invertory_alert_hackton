from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
from inventory.models import Product, StockAlert

class Command(BaseCommand):
    help = 'Check inventory levels and create alerts'
    
    def handle(self, *args, **options):
        # Check for low stock
        low_stock_products = Product.objects.filter(
            current_stock__lte=F('low_stock_threshold')
        )
        
        for product in low_stock_products:
            alert, created = StockAlert.objects.get_or_create(
                product=product,
                alert_type='LOW_STOCK',
                is_active=True,
                defaults={
                    'message': f'{product.name} is at low stock: {product.current_stock} units remaining'
                }
            )
            if created:
                self.stdout.write(f'Created low stock alert for {product.name}')
        
        # Check for products needing restock
        for product in Product.objects.all():
            restock_date = product.get_restock_recommendation()
            if restock_date and restock_date <= timezone.now().date():
                alert, created = StockAlert.objects.get_or_create(
                    product=product,
                    alert_type='RESTOCK_NEEDED',
                    is_active=True,
                    defaults={
                        'message': f'{product.name} needs restocking. Recommended restock date: {restock_date}'
                    }
                )
                if created:
                    self.stdout.write(f'Created restock alert for {product.name}')
        
        self.stdout.write(self.style.SUCCESS('Inventory check completed'))