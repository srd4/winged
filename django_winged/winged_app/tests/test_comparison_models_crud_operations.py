from django.test import TestCase
from ..models import (
    Item, SystemPrompt, Criterion, ItemVsTwoCriteriaAIComparison, CriterionVsItemsAIComparison
    )

from django.contrib.auth.models import User


class CriterionVsItemsAIComparisonCrudTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user('test_user', 'test_user@example.com', 'testpass123')
        self.criterion = Criterion.objects.create(name="test_criterion_1", user=self.user)

        self.item_1 = Item.objects.create(statement="test_item_1", user=self.user)
        self.item_2 = Item.objects.create(statement="test_item_2", user=self.user)

        self.item_choice = False

    def test_create_criterion_vs_items_comparison(self):
        comparison = CriterionVsItemsAIComparison.objects.create(
            ai_model="an_ai_model",
            criterion_statement_version=self.criterion.current_criterion_statement_version,
            item_compared_1_statement_version=self.item_1.current_statement_version,
            item_compared_2_statement_version=self.item_2.current_statement_version,
            item_choice=self.item_choice,
            execution_in_seconds=5
        )

        updated_comparison = CriterionVsItemsAIComparison.objects.get(pk=comparison.pk)

        # assert model was saved.
        self.assertEqual("an_ai_model", updated_comparison.ai_model)

        # assert user didnt make the comparison.
        self.assertFalse(updated_comparison.user_choice)

        # assert criterion and items.
        self.assertEqual(updated_comparison.criterion_statement_version, self.criterion.current_criterion_statement_version)
        self.assertEqual(updated_comparison.item_compared_1_statement_version, self.item_1.current_statement_version)
        self.assertEqual(updated_comparison.item_compared_2_statement_version, self.item_2.current_statement_version)

        # assert item chosen.
        self.assertEqual(updated_comparison.item_choice, self.item_choice)

        # assert one comparison was created.
        self.assertEqual(CriterionVsItemsAIComparison.objects.count(), 1)

        # assert only created comparison is ours.
        self.assertEqual(CriterionVsItemsAIComparison.objects.last(), comparison)


    def test_retrieve_criterion_vs_items_comparison(self):
        comparison = CriterionVsItemsAIComparison.objects.create(
            ai_model="an_ai_model",
            criterion_statement_version=self.criterion.current_criterion_statement_version,
            item_compared_1_statement_version=self.item_1.current_statement_version,
            item_compared_2_statement_version=self.item_2.current_statement_version,
            item_choice=self.item_choice,
            execution_in_seconds=5,
        )

        fetched_comparison = CriterionVsItemsAIComparison.objects.get(pk=comparison.pk)
        
        self.assertEqual(fetched_comparison, comparison)
        self.assertEqual(fetched_comparison.ai_model, "an_ai_model")

    def test_update_criterion_vs_items_comparison(self):
        comparison = CriterionVsItemsAIComparison.objects.create(
            ai_model="an_ai_model",
            criterion_statement_version=self.criterion.current_criterion_statement_version,
            item_compared_1_statement_version=self.item_1.current_statement_version,
            item_compared_2_statement_version=self.item_2.current_statement_version,
            item_choice=self.item_choice,
            execution_in_seconds=5,
        )

        updated_comparison = CriterionVsItemsAIComparison.objects.get(pk=comparison.pk)

        updated_comparison.ai_model = "updated_ai_model"
        updated_comparison.save()

        updated_comparison = CriterionVsItemsAIComparison.objects.get(pk=updated_comparison.pk)

        self.assertEqual(updated_comparison.ai_model, "updated_ai_model")



    def test_delete_criterion_vs_items_comparison(self):
        comparison = CriterionVsItemsAIComparison.objects.create(
            ai_model="an_ai_model",
            criterion_statement_version=self.criterion.current_criterion_statement_version,
            item_compared_1_statement_version=self.item_1.current_statement_version,
            item_compared_2_statement_version=self.item_2.current_statement_version,
            item_choice=self.item_choice,
            execution_in_seconds=5,
        )

        # assert exists.
        self.assertEqual(CriterionVsItemsAIComparison.objects.count(), 1)

        comparison.delete()
        # assert doesnt exist.
        self.assertEqual(CriterionVsItemsAIComparison.objects.count(), 0)


#item_vs_criteria
class ItemVsTwoCriteriaAIComparisonCRUDTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user', 'test_user@example.com', 'testpass123')
        
        # Assuming you have default instances of SystemPromptTextVersion, CriterionStatementVersion, and Item
        self.system_prompt = SystemPrompt.objects.create(text='TestPrompt', user=self.user)
        self.criterion_1 = Criterion.objects.create(statement='TestCriterion1', user=self.user)
        self.criterion_2 = Criterion.objects.create(statement='TestCriterion2', user=self.user)
        self.item = Item.objects.create(statement="Test Item", user=self.user)

    def test_create_item_vs_criteria_comparison(self):
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model='TestModel',
            system_prompt_text_version=self.system_prompt.current_prompt_text_version,
            criterion_statement_version_1=self.criterion_1.current_criterion_statement_version,
            criterion_statement_version_2=self.criterion_2.current_criterion_statement_version,
            item_compared_statement_version=self.item.current_statement_version,
            criterion_choice=True
        )
        self.assertEqual(ItemVsTwoCriteriaAIComparison.objects.count(), 1)
        self.assertEqual(ItemVsTwoCriteriaAIComparison.objects.last(), comparison)

    def test_read_item_vs_criteria_comparison(self):
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model='TestModel',
            system_prompt_text_version=self.system_prompt.current_prompt_text_version,
            criterion_statement_version_1=self.criterion_1.current_criterion_statement_version,
            criterion_statement_version_2=self.criterion_2.current_criterion_statement_version,
            item_compared_statement_version=self.item.current_statement_version,
            criterion_choice=True
        )
        fetched_comparison = ItemVsTwoCriteriaAIComparison.objects.get(id=comparison.id)
        self.assertEqual(fetched_comparison.ai_model, 'TestModel')

    def test_update_item_vs_criteria_comparison(self):
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model='TestModel',
            system_prompt_text_version=self.system_prompt.current_prompt_text_version,
            criterion_statement_version_1=self.criterion_1.current_criterion_statement_version,
            criterion_statement_version_2=self.criterion_2.current_criterion_statement_version,
            item_compared_statement_version=self.item.current_statement_version,
            criterion_choice=True
        )
        comparison.ai_model = 'UpdatedModel'
        comparison.save()
        fetched_comparison = ItemVsTwoCriteriaAIComparison.objects.get(id=comparison.id)
        self.assertEqual(fetched_comparison.ai_model, 'UpdatedModel')

    def test_delete_item_vs_criteria_comparison(self):
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model='TestModel',
            system_prompt_text_version=self.system_prompt.current_prompt_text_version,
            criterion_statement_version_1=self.criterion_1.current_criterion_statement_version,
            criterion_statement_version_2=self.criterion_2.current_criterion_statement_version,
            item_compared_statement_version=self.item.current_statement_version,
            criterion_choice=True
        )
        comparison.delete()
        self.assertEqual(ItemVsTwoCriteriaAIComparison.objects.count(), 0)
