# Generated by Django 4.2.3 on 2023-09-01 00:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('winged_app', '0019_alter_itemvstwocriteriaaicomparison_response'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='criteriastatementversion',
            name='parent_criteria',
        ),
        migrations.RemoveField(
            model_name='systempromptversion',
            name='parent_prompt',
        ),
    ]
