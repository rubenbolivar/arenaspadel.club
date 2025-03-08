# Generated by Django 4.2.18 on 2025-01-21 22:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0003_remove_reservation_total_price_and_more'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='reservation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment_set', to='reservations.reservation', verbose_name='reservation'),
        ),
    ]
