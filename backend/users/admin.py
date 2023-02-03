from django.contrib import admin

from users.models import Subscription, User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name'
    )
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')
    empty_value_display = '-empty-'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'author', 'user',
    )
    search_fields = ('author',)
    list_filter = ('author', 'user',)
    empty_value_display = '-empty-'
