# Generated by Django 4.2.1 on 2023-08-14 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_alter_contact_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adress',
            name='order',
        ),
        migrations.AddField(
            model_name='adress',
            name='order',
            field=models.ManyToManyField(related_name='adress', to='backend.order'),
        ),
    ]
