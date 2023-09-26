from django.test import TestCase, tag
from ..models import (
    Container, Item, StatementVersion, SpectrumType, SpectrumValue,
    SystemPromptTextVersion, SystemPrompt, CriteriaStatementVersion,
    Criteria, ItemVsTwoCriteriaAIComparison
    )
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


class ModelsCreationTest(TestCase):
    def setUp(self):
        self.first_user = User.objects.create_user('first_user', 'first_user@example.com', 'testpass')
        self.second_user = User.objects.create_user('second_user', 'second_user@example.com', 'testpass')

        self.first_user_container = Container.objects.create(name="first_user_container", user=self.first_user)
        self.second_user_container = Container.objects.create(name="second_user_container", user=self.second_user)

        self.spectrum_type = SpectrumType.objects.create(name="Test SpectrumType", description="Test Description", user=self.first_user)

        for i in range(7):
            Item.objects.create(statement=f"first_user_item_{i}", actionable=True, parent_container=self.first_user_container, user=self.first_user)
        for i in range(7, 14):
            Item.objects.create(statement=f"second_user_item{i}", actionable=True, parent_container=self.second_user_container, user=self.second_user)

    def test_containers_created(self):
        self.assertTrue(Container.objects.filter(name="first_user_container", user=self.first_user).exists())
        self.assertTrue(Container.objects.filter(name="second_user_container", user=self.second_user).exists())

    def test_items_created(self):
        self.assertEqual(Item.objects.filter(user=self.first_user).count(), 7)
        self.assertEqual(Item.objects.filter(user=self.second_user).count(), 7)

    def test_statement_version_creation(self):
        item = Item.objects.create(statement="Test Item", user=self.first_user)
        statement_version = StatementVersion.objects.create(statement="Test Statement", parent_item=item, user=self.first_user)

        self.assertEqual(statement_version.statement, "Test Statement")
        self.assertEqual(statement_version.parent_item, item)
        self.assertEqual(statement_version.user, self.first_user)

    def test_spectrum_type_creation(self):
        self.assertEqual(self.spectrum_type.name, "Test SpectrumType")
        self.assertEqual(self.spectrum_type.description, "Test Description")
        self.assertEqual(self.spectrum_type.user, self.first_user)

    def test_spectrum_value_creation(self):
        item = Item.objects.create(statement="Test Item", user=self.first_user)
        spectrum_value = SpectrumValue.objects.create(value=42, spectrum_type=self.spectrum_type, parent_item=item, user=self.first_user)
        self.assertEqual(spectrum_value.value, 42)
        self.assertEqual(spectrum_value.spectrum_type, self.spectrum_type)
        self.assertEqual(spectrum_value.parent_item, item)
        self.assertEqual(spectrum_value.user, self.first_user)

    def test_system_prompt_text_version_creation(self):
        parent_prompt = SystemPrompt.objects.create(
            name="testPrompt",
            ai_model="testAi",
            user=self.first_user,
            )

        system_prompt_text_version = SystemPromptTextVersion.objects.create(
            text="test prompt text version",
            parent_prompt=parent_prompt,
            user=self.first_user
            )
        # Prompt text holds.
        self.assertEqual(system_prompt_text_version.text, "test prompt text version")

        # Parent prompt holds.
        self.assertEqual(system_prompt_text_version.parent_prompt, parent_prompt)

        # User holds.
        self.assertEqual(system_prompt_text_version.user, self.first_user)
        self.assertEqual(parent_prompt.user, self.first_user)

        # SystemPromptTextVersion holds
        self.assertEqual(parent_prompt.prompt_text_version, system_prompt_text_version)

        # Ai model holds
        self.assertEqual(parent_prompt.ai_model, "testAi")


    def test_criteria_statement_version_creation(self):
        parent_criteria = Criteria.objects.create(
            name="test_criteria",
            user=self.first_user,
        )

        criteria_statement_version = CriteriaStatementVersion.objects.create(
            statement="test_statement",
            parent_criteria=parent_criteria,
            user=self.first_user,
        )

        # Assert Criteria statement.
        self.assertEqual(criteria_statement_version.statement, "test_statement")

        # Assert user.
        self.assertEqual(criteria_statement_version.user, self.first_user)
        self.assertEqual(parent_criteria.user, self.first_user)

        # Assert CriteriaStatementVersion.
        self.assertEqual(parent_criteria.criteria_statement_version, criteria_statement_version)

        # Assert name.
        self.assertEqual(parent_criteria.name, "test_criteria")
        self.assertEqual(parent_criteria.name, criteria_statement_version.parent_criteria.name)


    def test_system_prompt_creation(self):
        system_prompt = SystemPrompt.objects.create(
            name="testPrompt",
            ai_model="ai-model",
            user=self.first_user,
        )

        # Assert name.
        self.assertEqual(system_prompt.name, "testPrompt")

        # Assert ai model.
        self.assertEqual(system_prompt.ai_model, "ai-model")

        # Assert user.
        self.assertEqual(system_prompt.user, self.first_user)


    def test_criteria_creation(self):
        criteria = Criteria.objects.create(
            name="test_criteria",
            user=self.first_user,
        )
        
        # Assert name.
        self.assertEqual(criteria.name,  "test_criteria")

        # Assert user.
        self.assertEqual(criteria.user, self.first_user)



class ModelsRetrievalTest(TestCase):
    def setUp(self):
        self.first_user = User.objects.create_user('first_user', 'first_user@example.com', 'testpass')
        self.second_user = User.objects.create_user('second_user', 'second_user@example.com', 'testpass')

        self.first_user_container = Container.objects.create(name="first_user_container", user=self.first_user)
        self.second_user_container = Container.objects.create(name="second_user_container", user=self.second_user)

        self.spectrum_type = SpectrumType.objects.create(name="Test SpectrumType", description="Test Description", user=self.first_user)
        self.first_user_item = Item.objects.create(statement="Test Item", parent_container=self.first_user_container, user=self.first_user)
        self.second_user_item = Item.objects.create(statement="Test Item", parent_container=self.second_user_container, user=self.second_user)

    def test_system_prompt_text_version_retrieval(self):
        parent_prompt = SystemPrompt.objects.create(
            name="testPrompt",
            ai_model="testAi",
            user=self.first_user,
            )

        SystemPromptTextVersion.objects.create(
            text="test prompt text version",
            parent_prompt=parent_prompt,
            user=self.first_user
            )
        
        self.assertEqual(SystemPromptTextVersion.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(SystemPromptTextVersion.objects.filter(user=self.second_user).count(), 0)

    def test_criteria_statement_version_retrieval(self):
        parent_criteria = Criteria.objects.create(
            name="test_criteria",
            user=self.second_user,
        )

        CriteriaStatementVersion.objects.create(
            statement="test_statement",
            parent_criteria=parent_criteria,
            user=self.second_user,
        )

        self.assertEqual(CriteriaStatementVersion.objects.filter(user=self.first_user).count(), 0)
        self.assertEqual(CriteriaStatementVersion.objects.filter(user=self.second_user).count(), 1)

    def test_system_prompt_retrieval(self):
        SystemPrompt.objects.create(
            name="testPrompt",
            ai_model="ai-model",
            user=self.first_user,
        )

        self.assertEqual(SystemPrompt.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(SystemPrompt.objects.filter(user=self.second_user).count(), 0)

    def test_criteria_retrieval(self):
        Criteria.objects.create(
            name="test_criteria",
            user=self.second_user,
        )

        self.assertEqual(Criteria.objects.filter(user=self.first_user).count(), 0)
        self.assertEqual(Criteria.objects.filter(user=self.second_user).count(), 1)

    def test_containers_retrieval(self):
        self.assertEqual(Container.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(Container.objects.filter(user=self.second_user).count(), 1)

    def test_items_retrieval(self):
        self.assertEqual(Item.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(Item.objects.filter(user=self.second_user).count(), 1)

    def test_statement_version_retrieval(self):
        StatementVersion.objects.create(statement="Test Statement", parent_item=self.first_user_item, user=self.first_user)
        self.assertEqual(StatementVersion.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(StatementVersion.objects.filter(user=self.second_user).count(), 0)

    def test_spectrum_type_retrieval(self):
        self.assertEqual(SpectrumType.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(SpectrumType.objects.filter(user=self.second_user).count(), 0)

    def test_spectrum_value_retrieval(self):
        SpectrumValue.objects.create(value=42, spectrum_type=self.spectrum_type, parent_item=self.first_user_item, user=self.first_user)
        self.assertEqual(SpectrumValue.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(SpectrumValue.objects.filter(user=self.second_user).count(), 0)


class ModelsUpdateTest(TestCase):
    def setUp(self):
        self.first_user = User.objects.create_user('first_user', 'first_user@example.com', 'testpass')
        self.second_user = User.objects.create_user('second_user', 'second_user@example.com', 'testpass')

        self.first_user_container = Container.objects.create(name="first_user_container", user=self.first_user)
        self.second_user_container = Container.objects.create(name="second_user_container", user=self.second_user)

        self.first_user_item = Item.objects.create(statement="Test Item", parent_container=self.first_user_container, user=self.first_user)
        self.spectrum_type = SpectrumType.objects.create(name="Test SpectrumType", description="Test Description", user=self.first_user)
        self.spectrum_value = SpectrumValue.objects.create(value=42, spectrum_type=self.spectrum_type, parent_item=self.first_user_item, user=self.first_user)

        self.client = APIClient()

    def test_system_prompt_text_version_update(self):
        system_prompt_text_version = SystemPromptTextVersion.objects.create(
            text="test prompt text version",
            user=self.first_user,
            )
        
        # Assert initial .text
        self.assertEqual(system_prompt_text_version.text, "test prompt text version")

        system_prompt_text_version.text = "second text"
        system_prompt_text_version.save()
    
        # Assert change -update.
        self.assertEqual(system_prompt_text_version.text, "second text")


    def test_criteria_statement_version_update(self):
        criteria_statement_version = CriteriaStatementVersion.objects.create(
            statement="test_statement",
            user=self.second_user,
        )

        # Assert initial.
        self.assertEqual(criteria_statement_version.statement, "test_statement")

        criteria_statement_version.statement = "second statement"

        # Assert change.
        self.assertEqual(criteria_statement_version.statement, "second statement")


    def test_system_prompt_update(self):
        system_prompt = SystemPrompt.objects.create(
            name="testPrompt",
            ai_model="ai-model",
            user=self.first_user,
        )

        # Assert initial.
        self.assertEqual(system_prompt.name, "testPrompt")

        system_prompt.name = "second testPrompt"

        # Assert change.
        self.assertEqual(system_prompt.name, "second testPrompt")


    def test_criteria_update(self):
        criteria = Criteria.objects.create(
            name="test_criteria",
            user=self.second_user,
        )

        # Assert initial.
        self.assertEqual(criteria.name, "test_criteria")

        criteria.name = "second test_criteria"

        # Assert change.
        self.assertEqual(criteria.name, "second test_criteria")


    def test_container_update(self):
        self.first_user_container.name = "Updated Name"
        self.first_user_container.save()
        self.assertEqual(Container.objects.get(pk=self.first_user_container.pk).name, "Updated Name")

    def test_item_update(self):
        self.first_user_item.statement = "Updated Statement"
        self.first_user_item.save()
        self.assertEqual(Item.objects.get(pk=self.first_user_item.pk).statement, "Updated Statement")

    def test_statement_version_update(self):
        statement_version = StatementVersion.objects.create(statement="Test Statement", parent_item=self.first_user_item, user=self.first_user)
        statement_version.statement = "Updated Statement Version"
        statement_version.save()
        self.assertEqual(StatementVersion.objects.get(pk=statement_version.pk).statement, "Updated Statement Version")

    def test_spectrum_type_update(self):
        self.spectrum_type.name = "Updated SpectrumType"
        self.spectrum_type.save()
        self.assertEqual(SpectrumType.objects.get(pk=self.spectrum_type.pk).name, "Updated SpectrumType")

    def test_spectrum_value_update(self):
        self.spectrum_value.value = 84
        self.spectrum_value.save()
        self.assertEqual(SpectrumValue.objects.get(pk=self.spectrum_value.pk).value, 84)

    def test_unauthorized_container_update(self):
        # Authenticate as the second user
        self.client.force_authenticate(user=self.second_user)
        # Attempt to update a container owned by the first user
        url = reverse('containers-detail', kwargs={'pk': self.first_user_container.pk})
        response = self.client.patch(url, {'name': 'Unauthorized Update'})
        # Assert that the update was not allowed
        self.assertNotEqual(response.status_code, 200)
        # Refresh the container from the database to get the latest data
        self.first_user_container.refresh_from_db()
        # Assert that the name has not changed
        self.assertEqual(self.first_user_container.name, 'first_user_container')

class ModelsDeletionTest(TestCase):
    def setUp(self):
        self.first_user = User.objects.create_user('first_user', 'first_user@example.com', 'testpass')
        self.second_user = User.objects.create_user('second_user', 'second_user@example.com', 'testpass')

        self.first_user_container = Container.objects.create(name="first_user_container", user=self.first_user)
        self.second_user_container = Container.objects.create(name="second_user_container", user=self.second_user)
        self.first_user_item = Item.objects.create(statement="Test Item", parent_container=self.first_user_container, user=self.first_user)
        self.spectrum_type = SpectrumType.objects.create(name="Test SpectrumType", description="Test Description", user=self.first_user)
        self.spectrum_value = SpectrumValue.objects.create(value=42, spectrum_type=self.spectrum_type, parent_item=self.first_user_item, user=self.first_user)
        self.statement_version = StatementVersion.objects.create(statement="Test Statement", parent_item=self.first_user_item, user=self.first_user)

        self.client = APIClient()

    def test_authorized_container_deletion(self):
        self.client.force_authenticate(user=self.first_user)
        url = reverse('containers-detail', kwargs={'pk': self.first_user_container.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Container.objects.filter(pk=self.first_user_container.pk).exists())

    def test_unauthorized_container_deletion(self):
        self.client.force_authenticate(user=self.second_user)
        url = reverse('containers-detail', kwargs={'pk': self.first_user_container.pk})
        response = self.client.delete(url)
        self.assertNotEqual(response.status_code, 204)
        self.assertTrue(Container.objects.filter(pk=self.first_user_container.pk).exists())

    def test_authorized_item_deletion(self):
        self.client.force_authenticate(user=self.first_user)
        url = reverse('items-detail', kwargs={'pk': self.first_user_item.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Item.objects.filter(pk=self.first_user_item.pk).exists())

    def test_unauthorized_item_deletion(self):
        self.client.force_authenticate(user=self.second_user)
        url = reverse('items-detail', kwargs={'pk': self.first_user_item.pk})
        response = self.client.delete(url)
        self.assertNotEqual(response.status_code, 204)
        self.assertTrue(Item.objects.filter(pk=self.first_user_item.pk).exists())

    def test_authorized_spectrum_type_deletion(self):
        self.client.force_authenticate(user=self.first_user)
        url = reverse('spectrumtypes-detail', kwargs={'pk': self.spectrum_type.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(SpectrumType.objects.filter(pk=self.spectrum_type.pk).exists())

    def test_unauthorized_spectrum_type_deletion(self):
        self.client.force_authenticate(user=self.second_user)
        url = reverse('spectrumtypes-detail', kwargs={'pk': self.spectrum_type.pk})
        response = self.client.delete(url)
        self.assertNotEqual(response.status_code, 204)
        self.assertTrue(SpectrumType.objects.filter(pk=self.spectrum_type.pk).exists())

    def test_authorized_spectrum_value_deletion(self):
        self.client.force_authenticate(user=self.first_user)
        url = reverse('spectrumvalues-detail', kwargs={'pk': self.spectrum_value.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(SpectrumValue.objects.filter(pk=self.spectrum_value.pk).exists())

    def test_unauthorized_spectrum_value_deletion(self):
        self.client.force_authenticate(user=self.second_user)
        url = reverse('spectrumvalues-detail', kwargs={'pk': self.spectrum_value.pk})
        response = self.client.delete(url)
        self.assertNotEqual(response.status_code, 204)
        self.assertTrue(SpectrumValue.objects.filter(pk=self.spectrum_value.pk).exists())

    def test_authorized_statement_version_deletion(self):
        self.client.force_authenticate(user=self.first_user)
        url = reverse('statementversions-detail', kwargs={'pk': self.statement_version.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(StatementVersion.objects.filter(pk=self.statement_version.pk).exists())

    def test_unauthorized_statement_version_deletion(self):
        self.client.force_authenticate(user=self.second_user)
        url = reverse('statementversions-detail', kwargs={'pk': self.statement_version.pk})
        response = self.client.delete(url)
        self.assertNotEqual(response.status_code, 204)
        self.assertTrue(StatementVersion.objects.filter(pk=self.statement_version.pk).exists())
        

    def test_criteria_deletion(self):
        criteria = Criteria.objects.create(
            name='TestCriteria',
            user=self.first_user
        )
        criteria.delete()
        self.assertEqual(Criteria.objects.count(), 0)

    def test_criteria_statement_version_deletion(self):
        criteria = Criteria.objects.create(
            name='TestCriteria',
            user=self.first_user
        )
        statement_version = CriteriaStatementVersion.objects.create(
            statement='TestStatement',
            parent_criteria=criteria,
            user=self.first_user
        )
        statement_version.delete()
        self.assertEqual(CriteriaStatementVersion.objects.count(), 0)

    def test_system_prompt_deletion(self):
        system_prompt = SystemPrompt.objects.create(
            name='TestPrompt',
            ai_model='TestModel',
            user=self.first_user
        )
        system_prompt.delete()
        self.assertEqual(SystemPrompt.objects.count(), 0)

    def test_system_prompt_text_version_deletion(self):
        system_prompt = SystemPrompt.objects.create(
            name='TestPrompt',
            ai_model='TestModel',
            user=self.first_user
        )
        text_version = SystemPromptTextVersion.objects.create(
            text='TestText',
            parent_prompt=system_prompt,
            user=self.first_user
        )
        text_version.delete()
        self.assertEqual(SystemPromptTextVersion.objects.count(), 0)


class ItemVsTwoCriteriaAIComparisonCRUDTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user', 'test_user@example.com', 'testpass123')
        
        # Assuming you have default instances of SystemPromptTextVersion, CriteriaStatementVersion, and Item
        self.system_prompt = SystemPromptTextVersion.objects.create(text='TestPrompt', user=self.user)
        self.criteria_1 = CriteriaStatementVersion.objects.create(statement='TestCriteria1', user=self.user)
        self.criteria_2 = CriteriaStatementVersion.objects.create(statement='TestCriteria2', user=self.user)
        self.item = Item.objects.create(statement="Test Item", user=self.user)  # I've made assumptions based on your earlier code about the Item model's fields

    def test_create_comparison(self):
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model='TestModel',
            system_prompt=self.system_prompt,
            criteria_1=self.criteria_1,
            criteria_2=self.criteria_2,
            item_compared=self.item,
            criteria_choice=True
        )
        self.assertEqual(ItemVsTwoCriteriaAIComparison.objects.count(), 1)

    def test_read_comparison(self):
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model='TestModel',
            system_prompt=self.system_prompt,
            criteria_1=self.criteria_1,
            criteria_2=self.criteria_2,
            item_compared=self.item,
            criteria_choice=True
        )
        fetched_comparison = ItemVsTwoCriteriaAIComparison.objects.get(id=comparison.id)
        self.assertEqual(fetched_comparison.ai_model, 'TestModel')

    def test_update_comparison(self):
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model='TestModel',
            system_prompt=self.system_prompt,
            criteria_1=self.criteria_1,
            criteria_2=self.criteria_2,
            item_compared=self.item,
            criteria_choice=True
        )
        comparison.ai_model = 'UpdatedModel'
        comparison.save()
        fetched_comparison = ItemVsTwoCriteriaAIComparison.objects.get(id=comparison.id)
        self.assertEqual(fetched_comparison.ai_model, 'UpdatedModel')

    def test_delete_comparison(self):
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model='TestModel',
            system_prompt=self.system_prompt,
            criteria_1=self.criteria_1,
            criteria_2=self.criteria_2,
            item_compared=self.item,
            criteria_choice=True
        )
        comparison.delete()
        self.assertEqual(ItemVsTwoCriteriaAIComparison.objects.count(), 0)
