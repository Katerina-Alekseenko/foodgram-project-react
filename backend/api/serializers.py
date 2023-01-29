import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ListCart, Tag)
from users.models import Subscription, User


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для кодирования изображения в base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='photo.' + ext)

        return super().to_internal_value(data)


class UsersSerializer(UserSerializer):
    """ Сериализатор модели пользователя. """
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        if (self.context.get('request')
           and not self.context['request'].user.is_anonymous):
            return Subscription.objects.filter(user=self.context['request'].user,
                                            author=obj).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра модели Тег. """
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра модели Ингредиенты. """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор модели, связывающей ингредиенты и рецепт. """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=IngredientInRecipe.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра модели Рецепт. """
    tags = TagSerializer(many=True)
    author = UsersSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        read_only=True,
        many=True,
        source='recipe_ingredient'
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(user=self.context['request'].user,
                                        recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and ListCart.objects.filter(
                user=self.context['request'].user,
                recipe=obj).exists()
        )

class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор добавления ингредиента в рецепт. """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
     )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор создания/обновления рецепта. """
    author = UserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate_ingredients(self, value):
        ingredients_list = []
        ingredients = value
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество должно быть равным или больше 1')
            id_to_check = ingredient['ingredient']['id']
            ingredient_to_check = Ingredient.objects.filter(id=id_to_check)
            if not ingredient_to_check.exists():
                raise serializers.ValidationError(
                    'Данного продукта нет в базе')
            if ingredient_to_check in ingredients_list:
                raise serializers.ValidationError(
                    'Данные продукты повторяются в рецепте')
            ingredients_list.append(ingredient_to_check)
        return value

    def create_ingredients(self, ingredients, recipe):
        for i in ingredients:
            ingredient = Ingredient.objects.get(id=i['id'])
            IngredientInRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=i['amount']
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(serializers.ModelSerializer):
    """ Сериализатор модели Favorite. """
    id = serializers.ReadOnlyField(
        source='favorite_recipe.id',
    )
    name = serializers.ReadOnlyField(
        source='favorite_recipe.name',
    )
    image = serializers.CharField(
        source='favorite_recipe.image',
        read_only=True,
    )
    cooking_time = serializers.ReadOnlyField(
        source='favorite_recipe.cooking_time',
    )

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if Favorite.objects.filter(
            user=user,
            favorite_recipe=recipe
        ).exists():
            raise serializers.ValidationError({
                'errors': 'Рецепт уже в избранном'})
        return data


class ListCartSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта в списоке покупок."""
    id = serializers.ReadOnlyField(
        source='recipe.id',
    )
    name = serializers.ReadOnlyField(
        source='recipe.name',
    )
    image = serializers.CharField(
        source='recipe.image',
        read_only=True,
    )
    cooking_time = serializers.ReadOnlyField(
        source='recipe.cooking_time',
    )

    class Meta:
        model = ListCart
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if ListCart.objects.filter(
            user=user,
            recipe=recipe
        ).exists():
            raise serializers.ValidationError({
                'errors': 'Рецепт уже добавлен в список покупок'})
        return data


class SubscriptionsSerializer(serializers.ModelSerializer):
    """ Сериализатор подписок пользователя. """
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    email = serializers.ReadOnlyField(source='author.email')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=obj.user,
            author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = Recipe.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return FavoriteSerializer(
            recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()
