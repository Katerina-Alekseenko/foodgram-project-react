# Generated by Django 4.1.5 on 2023-01-21 22:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_remove_listcart_user_listcart_unique_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={'ordering': ('name',), 'verbose_name': 'Ингредиент', 'verbose_name_plural': 'ingredients'},
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'ordering': ('name',), 'verbose_name': 'Тег', 'verbose_name_plural': 'Tags'},
        ),
    ]
