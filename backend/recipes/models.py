from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db.models import UniqueConstraint

User = get_user_model()


class Ingredient(models.Model):
    """ Модель ингредиента. """
    name = models.CharField(
        'Название ингредиента',
        max_length=200
    )
    measurement_unit = models.CharField(
        'Единицы измерения ингредиента',
        max_length=100
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'ingredients'

    def __str__(self) -> str:
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """ Модель тегов. """
    name = models.CharField(
        max_length=100,
        verbose_name='Название тега',
        unique=True
    )
    color = models.CharField(
        max_length=7,
        verbose_name='Цвет',
        unique=True
    )
    slug = models.SlugField(
        max_length=100,
        verbose_name='Slug',
        unique=True
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Tags'

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    """ Моодель рецептов. """
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=200
    )
    image = models.ImageField(
        blank=True,
        verbose_name='Изображение рецепта',
        upload_to='recipes/'
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Recipes'

    def __str__(self) -> str:
        return self.name


class IngredientInRecipe(models.Model):
    """ Модель ингредиента в рецепте. """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient_unique'
            )
        ]


class Favorite(models.Model):
    """ Модель избранного рецепта. """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_unique'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} добавил в избранное {self.recipe}'


class ListCart(models.Model):
    """ Модель корзины. """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_shopping_cart',
    )

    class Meta:
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique recipe in shopping cart')]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return (f'Пользователь: {self.user.username},'
                f'рецепт в списке: {self.recipe.name}')

