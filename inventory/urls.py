from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/manage/', views.products_management, name='products_management'),
    path('products/low-stock/', views.low_stock_management, name='low_stock_management'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/add-sale/', views.add_sale, name='add_sale'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    path('alerts/<int:alert_id>/resolve-with-restock/', views.resolve_alert_with_restock, name='resolve_alert_with_restock'),
    path('restock/', views.restock_view, name='restock'),
]