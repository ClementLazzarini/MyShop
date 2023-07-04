# Generated by Django 4.2 on 2023-05-23 10:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0002_cartitem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='products',
        ),
        migrations.AddField(
            model_name='cart',
            name='items',
            field=models.ManyToManyField(through='market.CartItem', to='market.product'),
        ),
    ]
