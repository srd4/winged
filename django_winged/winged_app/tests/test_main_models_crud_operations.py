from django.test import TestCase, tag
from ..models import (
    Container, Item, ItemStatementVersion, SpectrumType, SpectrumValue,
    SystemPromptTextVersion, SystemPrompt, CriterionStatementVersion,
    Criterion
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

        # Assert that just created Items have current_statement_version and with no statement
        self.assertEqual(Item.objects.last().current_statement_version.statement, None)

    def test_item_statement_version_created_on_item_created_and_saved(self):
        new_item = Item(statement="new_item's statement", user=self.first_user)

        # Assert no ItemStatementVersion on new_item.current_statement_version before saving it.
        self.assertIsNone(new_item.current_statement_version)

        new_item.save()

        # Fetch from db.
        updated_item = Item.objects.get(pk=new_item.pk)

        # Assert updated_item.current_statement_version has changed to something.
        self.assertIsNotNone(updated_item.current_statement_version)

        # Assert updated_item.current_statement_version has changed to be an ItemStatementVersion
        self.assertEqual(type(updated_item.current_statement_version), ItemStatementVersion)

        # Assert new updated_item.current_statement_version has no statement string
        self.assertIsNone(updated_item.current_statement_version.statement)

    def test_item_statement_version_created_on_item_updated(self):
        new_item = Item.objects.create(statement="new_item's statement", user=self.first_user)
        
        # Hold new_item.current_statement_version before droping it.
        first_statement_version = new_item.current_statement_version

        new_item.statement = "new_item's second statement"

        new_item.save()

        updated_item = Item.objects.get(pk=new_item.pk)

        second_statement_version = updated_item.current_statement_version

        # Assert current_statement_version has changed after update and save.
        self.assertNotEqual(first_statement_version, second_statement_version)

        # Assert first_statement_version was given a statement before being dropped from current_statement_version.
        self.assertIsNotNone(first_statement_version.statement)

        # Assert second_statement_version does not have a statement.
        self.assertIsNone(second_statement_version.statement)


    def test_item_statement_version_creation(self):
        item = Item.objects.create(statement="Test Item", user=self.first_user)
        statement_version = ItemStatementVersion.objects.create(statement="Test Statement", parent_item=item, user=self.first_user)

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

    def test_system_prompt_text_version_creation_on_system_prompt_creation(self):
        parent_prompt = SystemPrompt.objects.create(
            name="testPrompt",
            ai_model="testAi",
            user=self.first_user,
            )
        # Assert current_prompt_text_version is type SystemPromptTextVersion so has been created.
        self.assertEqual(type(parent_prompt.current_prompt_text_version), SystemPromptTextVersion)

        # Assert current_prompt_text_version has no text yet
        self.assertEqual(parent_prompt.current_prompt_text_version.text, None)

        # Assert current_prompt_text_version's parent is parent_prompt
        self.assertEqual(parent_prompt.current_prompt_text_version.parent_prompt, parent_prompt)

        # Assert user holds.
        self.assertEqual(parent_prompt.current_prompt_text_version.user, self.first_user)



    def test_criterion_statement_version_creation_on_criterion_creation(self):
        parent_criterion = Criterion.objects.create(
            name="test_criterion",
            user=self.first_user,
        )

        # Assert current_criterion_statement_version's type.
        self.assertEqual(type(parent_criterion.current_criterion_statement_version), CriterionStatementVersion)

        # Assert Criterion statement is None.
        self.assertIsNone(parent_criterion.current_criterion_statement_version.statement)

        # Assert user.
        self.assertEqual(parent_criterion.current_criterion_statement_version.user, self.first_user)
        self.assertEqual(parent_criterion.user, self.first_user)

        # Assert name.
        self.assertEqual(parent_criterion.name, "test_criterion")
        self.assertEqual(parent_criterion.name, parent_criterion.current_criterion_statement_version.parent_criterion.name)


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


    def test_criterion_creation(self):
        criterion = Criterion.objects.create(
            name="test_criterion",
            user=self.first_user,
        )
        
        # Assert name.
        self.assertEqual(criterion.name,  "test_criterion")

        # Assert user.
        self.assertEqual(criterion.user, self.first_user)



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
        
        self.assertEqual(SystemPromptTextVersion.objects.filter(user=self.first_user).count(), 2)
        self.assertEqual(SystemPromptTextVersion.objects.filter(user=self.second_user).count(), 0)

    def test_criterion_statement_version_retrieval(self):
        parent_criterion = Criterion.objects.create(
            name="test_criterion",
            user=self.second_user,
        )

        CriterionStatementVersion.objects.create(
            statement="test_statement",
            parent_criterion=parent_criterion,
            user=self.second_user,
        )

        self.assertEqual(CriterionStatementVersion.objects.filter(user=self.first_user).count(), 0)
        self.assertEqual(CriterionStatementVersion.objects.filter(user=self.second_user).count(), 2)
        self.assertEqual(parent_criterion.current_criterion_statement_version, CriterionStatementVersion.objects.first())

    def test_system_prompt_retrieval(self):
        SystemPrompt.objects.create(
            name="testPrompt",
            ai_model="ai-model",
            user=self.first_user,
        )

        self.assertEqual(SystemPrompt.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(SystemPrompt.objects.filter(user=self.second_user).count(), 0)

    def test_criterion_retrieval(self):
        Criterion.objects.create(
            name="test_criterion",
            user=self.second_user,
        )

        self.assertEqual(Criterion.objects.filter(user=self.first_user).count(), 0)
        self.assertEqual(Criterion.objects.filter(user=self.second_user).count(), 1)

    def test_containers_retrieval(self):
        self.assertEqual(Container.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(Container.objects.filter(user=self.second_user).count(), 1)

    def test_items_retrieval(self):
        self.assertEqual(Item.objects.filter(user=self.first_user).count(), 1)
        self.assertEqual(Item.objects.filter(user=self.second_user).count(), 1)

    def test_statement_version_retrieval(self):
        ItemStatementVersion.objects.create(statement="Test Statement", parent_item=self.first_user_item, user=self.first_user)
        # Assert there's another ItemStatementVersion created for first_user_item's current_statement_version on setUp
        self.assertTrue(ItemStatementVersion.objects.filter(parent_item=self.first_user_item).exists())
        # Assert two ItemStatementVersions created
        self.assertEqual(ItemStatementVersion.objects.filter(user=self.first_user).count(), 2)

        # Assert there's another ItemStatementVersion created for second_user_item's current_statement_version on setUp
        self.assertTrue(ItemStatementVersion.objects.get(parent_item=self.second_user_item))
        # Assert there's one ItemStatementVersions in name of second_user
        self.assertEqual(ItemStatementVersion.objects.filter(user=self.second_user).count(), 1)

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

        updated_instance = SystemPromptTextVersion.objects.get(pk=system_prompt_text_version.pk)
    
        # Assert change -update.
        self.assertEqual(updated_instance.text, "second text")

    def test_system_prompt_text_version_update_on_system_prompt_update(self):
        system_prompt = SystemPrompt.objects.create(
            name="testPrompt",
            text="first text",
            ai_model="ai-model",
            user=self.first_user,
        )

        initial_current_prompt_text_version = system_prompt.current_prompt_text_version

        # Assert system prompt version has None text.
        self.assertIsNone(initial_current_prompt_text_version.text)

        # Assert initial text.
        self.assertEqual(system_prompt.text, "first text")
        # Change text.
        system_prompt.text = "second text"
        system_prompt.save()
        # Retrieve change from db.
        updated_system_prompt = SystemPrompt.objects.get(pk=system_prompt.pk)
        # Assert text change.
        self.assertEqual(updated_system_prompt.text, "second text")
        
        # Assert system prompt version doesn't have None text anymore.
        self.assertEqual(initial_current_prompt_text_version.text, "first text")
        self.assertNotEqual(initial_current_prompt_text_version, updated_system_prompt.current_prompt_text_version)


    def test_criterion_statement_version_update(self):
        criterion_statement_version = CriterionStatementVersion.objects.create(
            statement="test_statement",
            user=self.second_user,
        )

        # Assert initial.
        self.assertEqual(criterion_statement_version.statement, "test_statement")

        criterion_statement_version.statement = "second statement"

        criterion_statement_version.save()

        updated_current_criterion_statement_version = CriterionStatementVersion.objects.get(pk=criterion_statement_version.pk)

        # Assert change.
        self.assertEqual(updated_current_criterion_statement_version.statement, "second statement")

    def test_criterion_statement_version_update_on_criterion_update(self):
        criterion = Criterion.objects.create(
            name="test_criterion",
            statement="first statement",
            user=self.first_user,
        )

        initial_current_criterion_statement_version = criterion.current_criterion_statement_version

        # Assert initial_current_criterion_statement_version is None.
        self.assertIsNone(initial_current_criterion_statement_version.statement)
        
        # Assert first statement.
        self.assertEqual(criterion.statement, "first statement")
        # Change statement.
        criterion.statement = "second statement"
        # Save change to database.
        criterion.save()
        # Fetch from db
        updated_criterion = Criterion.objects.get(pk=criterion.pk)
        # Assert change on databse-fetched instance
        self.assertEqual(updated_criterion.statement, "second statement")

        # Assert Criterion instance has a different current_criterion_statement_version
        self.assertNotEqual(initial_current_criterion_statement_version, updated_criterion.current_criterion_statement_version)
        # Assert initial_current_criterion_statement_version is not None anymore.
        self.assertEqual(initial_current_criterion_statement_version.statement, "first statement")
        # Assert new current_criterion_statement_version's statement is None.
        self.assertIsNone(updated_criterion.current_criterion_statement_version.statement)


    def test_system_prompt_update(self):
        system_prompt = SystemPrompt.objects.create(
            name="testPrompt",
            ai_model="ai-model",
            user=self.first_user,
        )
        initial_time = system_prompt.prompt_text_updated_at

        self.assertEqual(system_prompt.name, "testPrompt")# Assert initial.
        system_prompt.name = "second testPrompt"
        self.assertEqual(system_prompt.name, "second testPrompt")# Assert change.

        updated_system_prompt = SystemPrompt.objects.get(pk=system_prompt.pk)
        # Assert prompt_text_updated_at has changed and is now greater.
        self.assertGreaterEqual(updated_system_prompt.prompt_text_updated_at, initial_time)

    def test_criterion_update(self):
        criterion = Criterion.objects.create(
            name="test_criterion",
            user=self.second_user,
        )
        initial_time = criterion.statement_updated_at

        self.assertEqual(criterion.name, "test_criterion")# Assert initial.
        criterion.name = "second test_criterion"
        criterion.save()
        self.assertEqual(criterion.name, "second test_criterion")# Assert change.

        updated_criterion = Criterion.objects.get(pk=criterion.pk)
        self.assertGreaterEqual(updated_criterion.statement_updated_at, initial_time)


    def test_container_update(self):
        self.first_user_container.name = "Updated Name"
        self.first_user_container.save()

        updated_instance = Container.objects.get(pk=self.first_user_container.pk)

        self.assertEqual(updated_instance.name, "Updated Name")

    def test_item_update(self):
        first_item_statement_version = self.first_user_item.current_statement_version
        self.assertEqual(first_item_statement_version.statement, None)

        self.first_user_item.statement = "Updated Statement"
        self.first_user_item.save()
        # Assert update was made on appropiate object instance.
        self.assertEqual(Item.objects.get(pk=self.first_user_item.pk).statement, "Updated Statement")
        # Assert current_statement_version object has changed after save.
        second_item_statement_version = self.first_user_item.current_statement_version
        self.assertNotEqual(first_item_statement_version, second_item_statement_version)

        self.first_user_item.save()

        self.first_user_item.refresh_from_db()

        # Assert current_statement_version doesn't change if item.statement doesn't either.
        self.assertEqual(second_item_statement_version, self.first_user_item.current_statement_version)

        # Assert current_statement_version has no statement.
        self.assertIsNone(self.first_user_item.current_statement_version.statement)


    def test_statement_updated_at_on_item_update(self):
        initial_updated_at_time = self.first_user_item.statement_updated_at

        self.first_user_item.statement = "Another statement"
        self.first_user_item.save()

        updated_item = Item.objects.get(pk=self.first_user_item.pk)

        self.assertGreaterEqual(updated_item.statement_updated_at, initial_updated_at_time)

    def test_statement_version_update(self):
        statement_version = ItemStatementVersion.objects.create(statement="Test Statement", parent_item=self.first_user_item, user=self.first_user)
        statement_version.statement = "Updated Statement Version"
        statement_version.save()
        self.assertEqual(ItemStatementVersion.objects.get(pk=statement_version.pk).statement, "Updated Statement Version")

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
        self.statement_version = ItemStatementVersion.objects.create(statement="Test Statement", parent_item=self.first_user_item, user=self.first_user)

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
        url = reverse('itemstatementversions-detail', kwargs={'pk': self.statement_version.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ItemStatementVersion.objects.filter(pk=self.statement_version.pk).exists())

    def test_unauthorized_statement_version_deletion(self):
        self.client.force_authenticate(user=self.second_user)
        url = reverse('itemstatementversions-detail', kwargs={'pk': self.statement_version.pk})
        response = self.client.delete(url)
        self.assertNotEqual(response.status_code, 204)
        self.assertTrue(ItemStatementVersion.objects.filter(pk=self.statement_version.pk).exists())
        

    def test_criterion_deletion(self):
        criterion = Criterion.objects.create(
            name='TestCriterion',
            user=self.first_user
        )
        criterion.delete()
        self.assertEqual(Criterion.objects.count(), 0)

    def test_criterion_statement_version_deletion(self):
        criterion = Criterion.objects.create(
            name='TestCriterion',
            user=self.first_user
        )
        statement_version = CriterionStatementVersion.objects.create(
            statement='TestStatement',
            parent_criterion=criterion,
            user=self.first_user
        )

        self.assertEqual(CriterionStatementVersion.objects.count(), 2)

        statement_version.delete()
        self.assertEqual(CriterionStatementVersion.objects.count(), 1)

        criterion.current_criterion_statement_version.delete()
        self.assertEqual(CriterionStatementVersion.objects.count(), 0)


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
        self.assertEqual(SystemPromptTextVersion.objects.count(), 1)
