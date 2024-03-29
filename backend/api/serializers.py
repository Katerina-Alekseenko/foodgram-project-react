import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, IngredientInRecipe,
                            ListCart, Recipe, Tag)
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
    is_subscribed = serializers.SerializerMethodField()

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
            return Subscription.objects.filter(
                user=self.context['request'].user,
                author=obj
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра модели Tag. """
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра модели Ingredient. """
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


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор добавления ингредиента в рецепт. """
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
    """ Сериализатор просмотра модели Recipe. """
    tags = TagSerializer(read_only=True, many=True)
    author = UsersSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = AddIngredientRecipeSerializer(
        source='ingredientinrecipe_set',
        many=True,
        read_only=True
    )

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def validate(self, value):
        ingredient_list = []
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Количество должно быть равным или больше 1'})
        for ingredient_item in ingredients:
            id_to_check = ingredient_item['id']
            ingredient_to_check = Ingredient.objects.filter(id=id_to_check)
            if not ingredient_to_check.exists():
                raise serializers.ValidationError(
                    'Данного продукта нет в базе')
            if ingredient_to_check in ingredient_list:
                raise serializers.ValidationError(
                    'Данные продукты повторяются в рецепте')
            ingredient_list.append(ingredient_to_check)
        return value

    def create_ingredients(self, ingredients, recipe):
        for i in ingredients:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient_id=i.get('id'),
                amount=i.get('amount'),
            )

    def create(self, validated_data):
        image = validated_data.pop('image')

        recipe = Recipe.objects.create(
            image=image,
            **validated_data,
            author=self.context['request'].user
        )

        tags = self.initial_data.get('tags')
        recipe.tags.set(tags)
        self.create_ingredients(self.initial_data.get('ingredients'), recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.tags.clear()
        tags = self.initial_data.get('tags')
        instance.tags.set(tags)
        IngredientInRecipe.objects.filter(recipe=instance).all().delete()
        self.create_ingredients(self.initial_data.get('ingredients'), instance)
        instance.save()
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """ Сериализатор модели Favorite. """
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
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if Favorite.objects.filter(
            user=user,
            recipe=recipe
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


class SubscribeRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор подписок пользователя. """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsSerializer(serializers.ModelSerializer):
    """ Сериализатор подписки и отписки. """
    email = serializers.CharField(
        source='author.email',
        read_only=True)
    id = serializers.IntegerField(
        source='author.id',
        read_only=True)
    username = serializers.CharField(
        source='author.username',
        read_only=True)
    first_name = serializers.CharField(
        source='author.first_name',
        read_only=True)
    last_name = serializers.CharField(
        source='author.last_name',
        read_only=True)
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(
        source='author.recipe.count')

    class Meta:
        model = Subscription
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count',)

    def get_recipes(self, obj):
        recipes = obj.author.recipe.all()
        return SubscribeRecipeSerializer(
            recipes,
            many=True).data

    def get_is_subscribed(self, obj):
        subscribe = Subscription.objects.filter(
            user=self.context.get('request').user,
            author=obj.author
        )
        if subscribe:
            return True
        return False


class UserSubscriptionsSerializer(SubscriptionsSerializer):
    """ Сериализатор модели пользователя. """
    is_subscribed = serializers.SerializerMethodField()

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

    def get_recipes(self, obj):
        recipes = obj.recipe.all()
        return SubscribeRecipeSerializer(
            recipes,
            many=True).data

    def get_is_subscribed(self, obj):
        subscribe = Subscription.objects.filter(
            user=self.context.get('request').user,
            author=obj
        )
        if subscribe:
            return True
        return False
