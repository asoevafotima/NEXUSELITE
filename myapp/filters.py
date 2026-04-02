import django_filters
from .models import Resume, Category

class ResumeFilter(django_filters.FilterSet):
    full_name = django_filters.CharFilter(
        field_name='full_name', 
        lookup_expr='icontains', 
        label='Search by Name'
    )
    
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label='Search by Profession'
    )

    class Meta:
        model = Resume
        fields = ['full_name', 'category']