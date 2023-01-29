from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    """ Модель пользователя. """
    username = models.CharField(
        db_index=True,
        max_length=150,
        unique=True,
        verbose_name='Уникальное имя',
        help_text='Введите уникальное имя пользователя'
    )
    email = models.EmailField(
        db_index=True,
        unique=True,
        max_length=254,
        verbose_name='Электронная почта',
        help_text='Введите электронную почту пользователя'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        help_text='Введите имя пользователя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        help_text='Введите фамилию пользователя'
    )
    is_subscribed = models.BooleanField(
        default=False,
        verbose_name='Подписка на данного пользователя',
        help_text='Отметьте для подписки на данного пользователя'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password'
    )

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """ Модель подписок. """
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
        )
    author = models.ForeignKey(
        User,
        related_name='author',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='user_author_unique'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на {self.author}'
