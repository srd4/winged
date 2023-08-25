from django.test import TestCase, tag
from ..models import Container, Item, StatementVersion, SpectrumType, SpectrumValue
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




class ModelsRetrievalTest(TestCase):
    def setUp(self):
        self.first_user = User.objects.create_user('first_user', 'first_user@example.com', 'testpass')
        self.second_user = User.objects.create_user('second_user', 'second_user@example.com', 'testpass')

        self.first_user_container = Container.objects.create(name="first_user_container", user=self.first_user)
        self.second_user_container = Container.objects.create(name="second_user_container", user=self.second_user)

        self.spectrum_type = SpectrumType.objects.create(name="Test SpectrumType", description="Test Description", user=self.first_user)
        self.first_user_item = Item.objects.create(statement="Test Item", parent_container=self.first_user_container, user=self.first_user)
        self.second_user_item = Item.objects.create(statement="Test Item", parent_container=self.second_user_container, user=self.second_user)

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
