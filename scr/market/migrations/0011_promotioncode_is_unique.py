# Generated by Django 4.2 on 2023-06-07 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0010_promotioncode_end_date_promotioncode_min_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='promotioncode',
            name='is_unique',
            field=models.BooleanField(default=False),
        ),
    ]
