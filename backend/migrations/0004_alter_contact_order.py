# Generated by Django 4.2.1 on 2023-08-14 09:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0003_alter_adress_building_alter_adress_structure_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contact', to='backend.order'),
        ),
    ]