import django_filters
from .models import Car
from datetime import date


class CarFilter(django_filters.FilterSet):
    brand = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price_per_day', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price_per_day', lookup_expr='lte')
    min_year = django_filters.NumberFilter(field_name='year', lookup_expr='gte')

    class Meta:
        model = Car
        fields = ['brand', 'status']