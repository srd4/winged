# Generated by Django 4.2.3 on 2023-09-01 00:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('winged_app', '0018_criteria_criteriastatementversion_systemprompt_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemvstwocriteriaaicomparison',
            name='response',
            field=models.JSONField(default=None, null=True),
        ),
    ]