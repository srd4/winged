# Generated by Django 4.2.3 on 2023-08-10 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('winged_app', '0013_spectrumvalue_gpt_curated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='container',
            name='last_opened_at',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='statement_updated_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]