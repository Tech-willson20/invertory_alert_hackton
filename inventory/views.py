from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.generic import ListView
from django.db.models import Q, F
from datetime import timedelta
from django.core.exceptions import ValidationError
from .models import Product, Sale, StockAlert
from .forms import ProductForm, SaleForm, AddStockForm, CustomUserCreationForm, CustomAuthenticationForm

def user_login(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'inventory/login.html', {'form': form})

def user_signup(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully! Welcome, {user.first_name}!')
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'inventory/signup.html', {'form': form})

def user_logout(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

def resolve_alert(request, alert_id):
    alert = get_object_or_404(StockAlert, pk=alert_id)
    alert.resolve()
    messages.success(request, 'Alert resolved')
    return redirect('alerts')

def restock_view(request):
    """View to display all products that need restocking"""
    products_needing_restock = []
    
    for product in Product.objects.all():
        restock_date = product.get_restock_recommendation()
        if restock_date and restock_date <= timezone.now().date() + timedelta(days=14):
            products_needing_restock.append({
                'product': product,
                'restock_date': restock_date,
                'days_until_restock': (restock_date - timezone.now().date()).days,
                'urgency': 'critical' if restock_date <= timezone.now().date() + timedelta(days=3) else 
                          'high' if restock_date <= timezone.now().date() + timedelta(days=7) else 'medium'
            })
    
    # Sort by urgency and then by days until restock
    products_needing_restock.sort(key=lambda x: (x['urgency'] == 'medium', x['urgency'] == 'high', x['days_until_restock']))
# number of high urgency products
    high_urgency_count = sum(1 for p in products_needing_restock if p['urgency'] == 'high')
    medium_urgency_count = sum(1 for p in products_needing_restock if p['urgency'] == 'medium')
    # number of critical urgency products
    critical_urgency_count = sum(1 for p in products_needing_restock if p['urgency'] == 'critical')
    context = {
        'products_needing_restock': products_needing_restock,
        'total_products_needing_restock': len(products_needing_restock),
        'high_urgency_count': high_urgency_count,
        'medium_urgency_count': medium_urgency_count,
        'low_urgency_count': len(products_needing_restock) - high_urgency_count - medium_urgency_count,
        'critical_urgency_count': critical_urgency_count,
    }
    return render(request, 'inventory/restock.html', context)

def products_management(request):
    """View to manage products - list all products and add new ones"""
    # Handle adding new product
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" has been added successfully!')
            return redirect('products_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    
    # Get all products with search functionality
    products = Product.objects.all().order_by('-created_at')
    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)
    
    # Get statistics
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(
        current_stock__lte=F('low_stock_threshold')
    )
    low_stock_count = low_stock_products.count()
    out_of_stock_count = Product.objects.filter(current_stock=0).count()
    in_stock_count = Product.objects.filter(current_stock__gt=0).count()
    active_stock_count = in_stock_count - low_stock_count 
    
    context = {
        'products': products,
        'form': form,
        'search': search,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'active_stock_count': active_stock_count,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'inventory/products_management.html', context)

def low_stock_management(request):
    """View to manage low stock products and add stock"""
    # Handle adding stock to a product
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, pk=product_id)
        form = AddStockForm(request.POST)
        
        if form.is_valid():
            quantity_to_add = form.cleaned_data['quantity']
            notes = form.cleaned_data['notes']
            
            # Update the product stock
            old_stock = product.current_stock
            product.current_stock += quantity_to_add
            product.save()
            
            # Create a success message
            messages.success(
                request, 
                f'Added {quantity_to_add} units to {product.name}. '
                f'Stock updated from {old_stock} to {product.current_stock}.'
            )
            
            # If notes were provided, you could log them (optional)
            if notes:
                messages.info(request, f'Notes: {notes}')
            
            return redirect('low_stock_management')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    
    # Get all low stock products
    low_stock_products = Product.objects.filter(
        current_stock__lte=F('low_stock_threshold')
    ).order_by('current_stock')
    
    # Categorize products by enhanced urgency logic
    categorized_products = []
    out_of_stock_count = 0
    very_low_count = 0
    low_count = 0
    
    for product in low_stock_products:
        # Enhanced categorization logic
        if product.current_stock == 0:
            urgency = 'critical'
            urgency_text = 'Out of Stock'
            out_of_stock_count += 1
        elif product.current_stock <= (product.low_stock_threshold / 2):
            urgency = 'high'
            urgency_text = 'Very Low'
            very_low_count += 1
        else:
            urgency = 'medium'
            urgency_text = 'Low'
            low_count += 1
        
        # Calculate stock percentage
        stock_percentage = 0
        if product.low_stock_threshold > 0:
            stock_percentage = (product.current_stock / product.low_stock_threshold) * 100
        
        categorized_products.append({
            'product': product,
            'urgency': urgency,
            'urgency_text': urgency_text,
            'stock_percentage': stock_percentage
        })
    
    # Sort by urgency: critical first, then high (very low), then medium (low)
    urgency_order = {'critical': 0, 'high': 1, 'medium': 2}
    categorized_products.sort(key=lambda x: (urgency_order[x['urgency']], x['stock_percentage']))
    
    # Calculate total low stock count
    total_low_stock = low_stock_products.count()
    
    context = {
        'low_stock_products': categorized_products,
        'total_low_stock': total_low_stock,
        'out_of_stock_count': out_of_stock_count,
        'very_low_count': very_low_count,
        'low_count': low_count,
        'add_stock_form': AddStockForm(),
    }
    return render(request, 'inventory/low_stock_management.html', context)

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

@login_required
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

def resolve_alert_with_restock(request, alert_id):
    """Resolve an alert by adding stock to the product"""
    alert = get_object_or_404(StockAlert, pk=alert_id)
    product = alert.product
    
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        notes = request.POST.get('notes', '')
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            
            # Update product stock
            old_stock = product.current_stock
            product.current_stock += quantity
            product.save()
            
            # Resolve the alert
            alert.resolve()
            
            # Create success message
            messages.success(
                request,
                f'Successfully added {quantity} units to {product.name}. '
                f'Stock updated from {old_stock} to {product.current_stock}. Alert resolved!'
            )
            
            # Add notes message if provided
            if notes.strip():
                messages.info(request, f'Notes: {notes}')
            
            # Check if stock is now above threshold
            if product.current_stock > product.low_stock_threshold:
                messages.success(
                    request,
                    f'✅ {product.name} is now above the low stock threshold!'
                )
            else:
                messages.warning(
                    request,
                    f'⚠️ {product.name} is still below the low stock threshold. Consider adding more stock.'
                )
                
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid quantity.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('alerts')