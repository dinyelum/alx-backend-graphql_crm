import django_filters
from django.db.models import Q
from .models import Customer, Product, Order

class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    created_at_gte = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    phone_pattern = django_filters.CharFilter(method='filter_phone_pattern')
    
    class Meta:
        model = Customer
        fields = {
            'name': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
        }
    
    def filter_phone_pattern(self, queryset, name, value):
        """
        Custom filter for phone number patterns
        Example: filter phones starting with +1
        """
        if value == '+1':
            return queryset.filter(phone__startswith='+1')
        elif value.startswith('starts_with:'):
            prefix = value.replace('starts_with:', '')
            return queryset.filter(phone__startswith=prefix)
        elif value.startswith('contains:'):
            pattern = value.replace('contains:', '')
            return queryset.filter(phone__icontains=pattern)
        else:
            # Default: search for exact match or contains
            return queryset.filter(
                Q(phone__exact=value) | Q(phone__icontains=value)
            )

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    price_gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    stock_gte = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock_lte = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
        }
    
    def filter_low_stock(self, queryset, name, value):
        """
        Filter products with low stock (stock < 10)
        """
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

class OrderFilter(django_filters.FilterSet):
    total_amount_gte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_lte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    order_date_gte = django_filters.DateFilter(field_name='order_date', lookup_expr='gte')
    order_date_lte = django_filters.DateFilter(field_name='order_date', lookup_expr='lte')
    customer_name = django_filters.CharFilter(field_name='customer__name', lookup_expr='icontains')
    product_name = django_filters.CharFilter(field_name='products__name', lookup_expr='icontains')
    product_id = django_filters.UUIDFilter(field_name='products__id')
    
    class Meta:
        model = Order
        fields = {
            'total_amount': ['exact', 'gte', 'lte'],
            'order_date': ['exact', 'gte', 'lte'],
        }