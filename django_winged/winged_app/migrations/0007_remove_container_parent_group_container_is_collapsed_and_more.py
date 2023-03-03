# Generated by Django 4.1.6 on 2023-02-12 02:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('winged_app', '0006_rename_containercategory_containergroup_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='container',
            name='parent_group',
        ),
        migrations.AddField(
            model_name='container',
            name='is_collapsed',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='container',
            name='parent_container',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='winged_app.container'),
        ),
        migrations.DeleteModel(
            name='ContainerGroup',
        ),
    ]