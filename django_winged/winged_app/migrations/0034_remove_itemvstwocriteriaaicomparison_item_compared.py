# Generated by Django 4.2.5 on 2023-10-11 23:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('winged_app', '0033_remove_itemvstwocriteriaaicomparison_item_compared'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemvstwocriteriaaicomparison',
            name='item_compared',
        ),
    ]
