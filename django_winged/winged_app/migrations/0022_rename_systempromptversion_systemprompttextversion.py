# Generated by Django 4.2.3 on 2023-09-01 00:57

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('winged_app', '0021_criteriastatementversion_parent_criteria_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SystemPromptVersion',
            new_name='SystemPromptTextVersion',
        ),
    ]
