# Generated by Django 4.1.5 on 2023-01-31 00:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('winged_app', '0003_remove_container_is_collapsed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='containercategory',
            name='parent_category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='winged_app.containercategory'),
        ),
    ]
