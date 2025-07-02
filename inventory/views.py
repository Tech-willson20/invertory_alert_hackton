from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView
from django.db.models import Q, F
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from .models import Product, Sale, StockAlert
from .forms import ProductForm, SaleForm

class ProductListView(ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        queryset = Product.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['low_stock_products'] = Product.objects.filter(
            current_stock__lte=F('low_stock_threshold')
        )
        context['active_alerts'] = StockAlert.objects.filter(is_active=True)
        return context

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    recent_sales = product.sales.all()[:10]
    
    # Check for low stock and create alert if needed
    if product.is_low_stock:
        alert, created = StockAlert.objects.get_or_create(
            product=product,
            alert_type='LOW_STOCK',
            is_active=True,
            defaults={
                'message': f'{product.name} is running low on stock. Current: {product.current_stock}, Threshold: {product.low_stock_threshold}'
            }
        )
    
    context = {
        'product': product,
        'recent_sales': recent_sales,
        'daily_avg': product.get_daily_sales_average(),
        'stockout_date': product.predict_stockout_date(),
        'restock_date': product.get_restock_recommendation(),
    }
    return render(request, 'inventory/product_detail.html', context)

def add_sale(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.product = product
            try:
                sale.save()
                messages.success(request, f'Sale recorded: {sale.quantity} units of {product.name}')
                
                if product.is_low_stock:
                    StockAlert.objects.get_or_create(
                        product=product,
                        alert_type='LOW_STOCK',
                        is_active=True,
                        defaults={
                            'message': f'{product.name} is now at low stock level: {product.current_stock} units'
                        }
                    )
                
                return redirect('product_detail', pk=product.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = SaleForm()
    
    return render(request, 'inventory/add_sale.html', {'form': form, 'product': product})

def dashboard(request):
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(
        current_stock__lte=F('low_stock_threshold')
    ).count()
    active_alerts = StockAlert.objects.filter(is_active=True).count()
    recent_sales = Sale.objects.all()[:5]
    
    products_needing_restock = []
    for product in Product.objects.all():
        restock_date = product.get_restock_recommendation()
        if restock_date and restock_date <= timezone.now().date() + timedelta(days=7):
            products_needing_restock.append(product)
    
    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'active_alerts': active_alerts,
        'recent_sales': recent_sales,
        'products_needing_restock': products_needing_restock,
    }
    return render(request, 'inventory/dashboard.html', context)

def alerts_view(request):
    alerts = StockAlert.objects.filter(is_active=True)
    return render(request, 'inventory/alerts.html', {'alerts': alerts})

def resolve_alert(request, alert_id):
    alert = get_object_or_404(StockAlert, pk=alert_id)
    alert.resolve()
    messages.success(request, 'Alert resolved')
    return redirect('alerts')