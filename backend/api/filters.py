from django_filters import rest_framework as filter

from rest_framework.filters import SearchFilter
from recipes.models import Recipe


class RecipeFilter(filter.FilterSet):
    is_favorited = filter.NumberFilter(
        method='get_is_favorited'
    )
    tags = filter.AllValuesMultipleFilter(
        field_name='tags__slug',
    )
    is_in_shopping_cart = filter.NumberFilter(
        method='get_is_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'is_favorited',
            'author',
            'tags',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(favorites__user_id=user.id)
        return queryset.all()

    def get_is_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(shopping_cart__user_id=user.id)
        return queryset.all()
