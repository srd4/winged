# Generated by Django 4.2.3 on 2023-10-11 23:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('winged_app', '0034_remove_itemvstwocriteriaaicomparison_item_compared'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemvstwocriteriaaicomparison',
            name='item_compared_statement_version',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='winged_app.itemstatementversion'),
        ),
    ]