import logging

from http import HTTPStatus
from django.db.models import Sum
from django.shortcuts import get_object_or_404, get_list_or_404
from django.http import HttpResponse
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ListCart, Tag)
from users.models import Subscription, User
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import RecipesFilter
from api.paginations import CustomPagination
from api.mixins import CreateDestroyViewSet
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeSerializer, CreateRecipeSerializer,
                          ListCartSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UsersSerializer)


logger = logging.getLogger(__name__)


'''
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe,
                            ListCart, Tag)
from users.models import Subscription, User
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.paginations import CustomPagination
from api.mixins import CreateDestroyViewSet
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeSerializer, CreateRecipeSerializer,
                          ListCartSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UsersSerializer)
'''


class UsersViewSet(UserViewSet):
    """ Вьюсет для работы с пользователями """
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None
    http_method_names = ['get', 'post', 'delete', 'head']

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(methods=['POST', 'DELETE'],
            detail=True, )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(
            user=user, author=author)

        if request.method == 'POST':
            if subscription.exists():
                return Response({'error': 'Вы уже подписаны'},
                                status=status.HTTP_400_BAD_REQUEST)
            if user == author:
                return Response({'error': 'Невозможно подписаться на себя'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = SubscriptionsSerializer(
                author,
                context={'request': request}
            )
            Subscription.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Вы не подписаны на этого пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        follows = User.objects.filter(following__user=user)
        page = self.paginate_queryset(follows)
        serializer = SubscriptionsSerializer(
            page, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """ Вьюсет для рецептов. """

    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination
    queryset = Recipe.objects.all()
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        logger.debug('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! something error')
        if self.request.method == 'GET':
            return CreateRecipeSerializer
        return RecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context


'''
    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
        pagination_class=None)
    def download_file(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(
                'В корзине нет товаров', status=status.HTTP_400_BAD_REQUEST)

        text = 'Список покупок:\n\n'
        ingredient_name = 'recipe__recipe__ingredient__name'
        ingredient_unit = 'recipe__recipe__ingredient__measurement_unit'
        recipe_amount = 'recipe__recipe__amount'
        amount_sum = 'recipe__recipet__amount__sum'
        cart = user.shopping_cart.select_related('recipe').values(
            ingredient_name, ingredient_unit).annotate(Sum(
                recipe_amount)).order_by(ingredient_name)
        for _ in cart:
            text += (
                f'{_[ingredient_name]} ({_[ingredient_unit]})'
                f' — {_[amount_sum]}\n'
            )
        response = HttpResponse(text, content_type='text/plain')
        filename = 'shopping_list.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return
'''

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет для ингредиентов. """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None
    #filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет для тегов. """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class SubscribeViewSet(CreateDestroyViewSet):
    """ Вьюсет для подписок. """

    serializer_class = SubscriptionsSerializer

    permission_classes = [IsAuthenticated, ]
    pagination_class = CustomPagination

    def get_queryset(self, request):
        user = request.user
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        queryset = User.objects.filter(author__user=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['author_id'] = self.kwargs.get('user_id')
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            author=get_object_or_404(
                User,
                id=self.kwargs.get('user_id')
            )
        )

    @action(methods=('delete',), detail=True)
    def delete(self, request, user_id):
        get_object_or_404(User, id=user_id)
        if not Subscription.objects.filter(
                user=request.user, author_id=user_id).exists():
            return Response({'errors': 'Вы не были подписаны на автора'},
                            status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(
            Subscription,
            user=request.user,
            author_id=user_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteRecipeViewSet(CreateDestroyViewSet):
    """ Вьюсет для избранных рецептов. """

    serializer_class = FavoriteSerializer

    def get_queryset(self):
        user = self.request.user.id
        return Favorite.objects.filter(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            recipe=get_object_or_404(
                Recipe,
                id=self.kwargs.get('recipe_id')
            )
        )

    @action(methods=('delete',), detail=True)
    def delete(self, request, recipe_id):
        recipe = request.user
        if not recipe.favorites.select_related(
                'recipe').filter(
                    recipe_id=recipe_id).exists():
            return Response({'errors': 'Рецепт не в избранном'},
                            status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(
            Favorite,
            user=request.user,
            recipe_id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListCartViewSet(CreateDestroyViewSet):
    """ Вьюсет для корзины. """

    serializer_class = ListCartSerializer

    def get_queryset(self):
        user = self.request.user.id
        return ListCart.objects.filter(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            recipe=get_object_or_404(
                Recipe,
                id=self.kwargs.get('recipe_id')
            )
        )

    @action(methods=('delete',), detail=True)
    def delete(self, request, recipe_id):
        u = request.user
        if not u.shopping_cart.select_related(
                'recipe').filter(
                    recipe_id=recipe_id).exists():
            return Response({'errors': 'Рецепта нет в корзине'},
                            status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(
            ListCart,
            user=request.user,
            recipe=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

