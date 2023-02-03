from django.contrib import admin
from recipes.models import (Favorite, Ingredient, ListCart,
                            Recipe, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    empty_value_display = '--empty--'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'slug')
    empty_value_display = '--empty--'

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites')
    search_fields = ('name',)
    empty_value_display = '--empty--'

    def favorite_count(self, instance):
        return Favorite.objects.filter(recipe=instance).count()

@admin.register(Favorite)
class FavoritetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    empty_value_display = '--empty--'

@admin.register(ListCart)
class ListCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    empty_value_display = '--empty--'
