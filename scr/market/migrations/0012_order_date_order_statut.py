# Generated by Django 4.2 on 2023-06-08 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0011_promotioncode_is_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='statut',
            field=models.CharField(default='old', max_length=255),
            preserve_default=False,
        ),
    ]