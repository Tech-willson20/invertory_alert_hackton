from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    current_stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def is_low_stock(self):
        return self.current_stock <= self.low_stock_threshold
    
    def get_daily_sales_average(self, days=30):
        """Calculate average daily sales over the last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        sales = Sale.objects.filter(
            product=self,
            date__range=[start_date, end_date]
        ).aggregate(total=models.Sum('quantity'))
        
        total_sold = sales['total'] or 0
        return total_sold / days if days > 0 else 0
    
    def predict_stockout_date(self):
        """Predict when stock will run out based on average daily sales"""
        daily_avg = self.get_daily_sales_average()
        
        if daily_avg <= 0:
            return None
        
        days_until_stockout = self.current_stock / daily_avg
        return timezone.now().date() + timedelta(days=int(days_until_stockout))
    
    def get_restock_recommendation(self, lead_time_days=7):
        """Recommend when to restock based on lead time"""
        stockout_date = self.predict_stockout_date()
        
        if not stockout_date:
            return None
        
        restock_date = stockout_date - timedelta(days=lead_time_days)
        return max(restock_date, timezone.now().date())

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    quantity = models.PositiveIntegerField()
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} units on {self.date}"
    
    def save(self, *args, **kwargs):
        if self.pk is None:  # New sale
            if self.product.current_stock < self.quantity:
                raise ValidationError("Insufficient stock for this sale")
            self.product.current_stock -= self.quantity
            self.product.save()
        super().save(*args, **kwargs)

class StockAlert(models.Model):
    ALERT_TYPES = [
        ('LOW_STOCK', 'Low Stock'),
        ('RESTOCK_NEEDED', 'Restock Needed'),
        ('STOCKOUT_PREDICTED', 'Stockout Predicted'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_type} - {self.product.name}"
    
    def resolve(self):
        self.is_active = False
        self.resolved_at = timezone.now()
        self.save()