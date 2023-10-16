from django.db import migrations, transaction

def prepare_items(apps, schema_editor):
    Item = apps.get_model('winged_app', 'Item')
    ItemStatementVersion = apps.get_model('winged_app', 'ItemStatementVersion')
    
    for item in Item.objects.all():
        new_statement_version = ItemStatementVersion.objects.create(
            parent_item=item,
            user=item.user
        )
        item.current_statement_version = new_statement_version
        item.save()

class Migration(migrations.Migration):

    dependencies = [
        ('winged_app', '0031_itemvstwocriteriaaicomparison_item_compared_statement_version'),
    ]

    operations = [
        migrations.RunPython(prepare_items),
        
    ]