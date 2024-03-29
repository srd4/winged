# Generated by Django 4.2.5 on 2023-10-14 19:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('winged_app', '0035_alter_itemvstwocriteriaaicomparison_item_compared_statement_version'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemvstwocriteriaaicomparison',
            name='criteria_statement_version_1',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='first_criteria_one_item_vs_two_criteria_comparisons', to='winged_app.criteriastatementversion'),
        ),
        migrations.AlterField(
            model_name='itemvstwocriteriaaicomparison',
            name='criteria_statement_version_2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='second_criteria_one_item_vs_two_criteria_comparisons', to='winged_app.criteriastatementversion'),
        ),
        migrations.AlterField(
            model_name='itemvstwocriteriaaicomparison',
            name='item_compared_statement_version',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='one_item_vs_two_criteria_comparisons', to='winged_app.itemstatementversion'),
        ),
        migrations.CreateModel(
            name='CriterionVsItemsAIComparison',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ai_model', models.CharField(db_index=True, default=None, max_length=128, null=True)),
                ('user_choice', models.BooleanField(default=False)),
                ('item_choice', models.BooleanField(choices=[(True, 'Item 1'), (False, 'Item 2')], db_index=True, default=False)),
                ('response', models.JSONField(default=None, null=True)),
                ('execution_in_seconds', models.DecimalField(decimal_places=2, default=None, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('criterion_statement_version', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='criterion_comparisons', to='winged_app.criteriastatementversion')),
                ('item_compared_1_statement_version', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='first_item_statement_version_criterion_comparisons', to='winged_app.itemstatementversion')),
                ('item_compared_2_statement_version', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='second_item_statement_version_criterion_comparisons', to='winged_app.itemstatementversion')),
                ('system_prompt_text_version', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='winged_app.systemprompttextversion')),
            ],
        ),
    ]
