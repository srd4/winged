from rest_framework.test import APIClient
from django.test import TestCase, tag
from ..models import Container, Item, Criterion, DoublyLinkedListNode, SpectrumDoublyLinkedList
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.urls import reverse
from rest_framework.status import HTTP_202_ACCEPTED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from unittest.mock import patch, call
from threading import Thread


class TokenAuthenticationTest(TestCase):
    def setUp(self):
        self.first_user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
        self.second_user = User.objects.create_user('second_testuser', 'second_test@example.com', 'testpass')

        Container.objects.create(name="testuser_container", user=self.first_user)

        # Create tokens for both users
        self.first_user_token = Token.objects.create(user=self.first_user)
        self.second_user_token = Token.objects.create(user=self.second_user)
        
        self.client = APIClient()
        

    def test_user_creation(self):
        # The user created in setUp is in the test database, so we can query it here
        user = User.objects.get(username='testuser')
        user_2 = User.objects.get(username='second_testuser')

        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')

        self.assertEqual(user_2.email, 'second_test@example.com')
        self.assertEqual(user_2.username, 'second_testuser')


    def test_authenticated_endpoint(self):
        # Replace with an endpoint that requires authentication
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.first_user_token.key)
        response = self.client.get('/containerTrees/')
        self.assertEqual(response.status_code, 200)


    def test_unauthenticated_endpoint(self):
        response = self.client.get('/containerTrees/')
        self.assertEqual(response.status_code, 401)  # Forbidden
        self.assertIn('detail', response.json())
        self.assertEqual(response.json()['detail'], 'Authentication credentials were not provided.')


    def test_allowed_endpoint(self):
        # first user accessing his stuff.
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.first_user_token.key)

        container = Container.objects.filter(user=self.first_user).last()
        url = reverse("containers-detail", args=[container.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
    

    def test_not_allowed_endpoint(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.second_user_token.key)
        container = Container.objects.filter(user=self.first_user).last()

        url = reverse("containers-detail", args=[container.pk])

        response = self.client.get(url)

        # There is a container.
        self.assertIsNotNone(container, "Container is None")
        # It's owner is the second user.
        self.assertEqual(self.first_user, container.user)
        # Not the second user.
        self.assertNotEqual(self.second_user, container.user)

        # So we can't acces it.
        # 404 (and not 403) due to overriden get_queryset method on view -filter(user=self.request.user).
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], "Not found.")

    def test_token_association_with_user(self):
        # Ensure that the token for the first user is correctly associated
        token = Token.objects.get(user=self.first_user)
        self.assertEqual(token, self.first_user_token)

        # Ensure that the token for the second user is correctly associated
        token = Token.objects.get(user=self.second_user)
        self.assertEqual(token, self.second_user_token)


class ContainerTreeViewContainersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
        self.client = APIClient()

        for i in range(3):
            parent = Container.objects.create(name=f"testuser_parent_container_{i}", user=self.user)
            for e in range(4):
                Container.objects.create(name=f"testuser_child_container_{i}", user=self.user, parent_container=parent)

    
    def test_container_list(self):
        # Validate the custom list method retrieves correct containers.
        self.client.force_authenticate(user=self.user)

        url = reverse("containerTrees-list")

        response = self.client.get(url)

        ids = (i["id"] for i in response.data)

        for container in Container.objects.filter(pk__in=ids):
            self.assertEqual(container.parent_container, None)

        self.assertEqual(response.status_code, 200)


class MockThread(Thread):
    def start(self):
        self.run()

class CriterionVsItemsSortingScriptViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(username='user', password='password')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        self.container = Container.objects.create(name="Test Container", user=self.user)
        self.criterion = Criterion.objects.create(name="Test Criterion", user=self.user)
        self.criterion_statement_version = self.criterion.current_criterion_statement_version

        self.item1 = Item.objects.create(
            parent_container=self.container,
            user=self.user,
            actionable=self.container.is_on_actionables_tab,
            done=self.container.is_on_done_tab,
            archived=False
        )
        self.item2 = Item.objects.create(
            parent_container=self.container,
            user=self.user,
            actionable=self.container.is_on_actionables_tab,
            done=self.container.is_on_done_tab,
            archived=False
        )

        self.item3 = Item.objects.create(
            parent_container=self.container,
            user=self.user,
            actionable=self.container.is_on_actionables_tab,
            done=self.container.is_on_done_tab,
            archived=False
        )

        self.ai_model = "bart_large_mnli"

    def test_post(self):
        url = reverse('criterion-vs-items-sort', kwargs={'container_id': self.container.id, 'criterion_id': self.criterion.id, 'ai_model': self.ai_model})

        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        
    def test_post_with_invalid_container(self):
        url = reverse('criterion-vs-items-sort', kwargs={'container_id': 9999, 'criterion_id': self.criterion.id, 'ai_model': self.ai_model})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_with_invalid_criterion(self):
        url = reverse('criterion-vs-items-sort', kwargs={'container_id': self.container.id, 'criterion_id': 9999, 'ai_model': self.ai_model})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_post_with_invalid_ai_model(self):
        url = reverse('criterion-vs-items-sort', kwargs={'container_id': self.container.id, 'criterion_id': self.criterion.id, 'ai_model': 'invalid_ai_model'})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)


    @patch('threading.Thread', new=MockThread)
    @patch('winged_app.models.SpectrumDoublyLinkedList.insert')
    def test_post_with_mocked_insert_and_thread(self, mock_insert):
        mock_insert.return_value = None  # or whatever you want the mock to return

        url = reverse('criterion-vs-items-sort', kwargs={'container_id': self.container.id, 'criterion_id': self.criterion.id, 'ai_model': self.ai_model})
        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        
        # Will have to change None for the actual callable comparator function.
        """expected_calls = [call(self.item1, None), call(self.item2, None)]
        mock_insert.assert_has_calls(expected_calls, any_order=True)"""

class ContainerItemListAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create two users
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')

        # Create tokens for the users
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        # Create containers for both users
        self.container1 = Container.objects.create(name='container1', user=self.user1)
        self.container2 = Container.objects.create(name='container2', user=self.user2)

        # Create items within the containers
        self.item1 = Item.objects.create(statement='item1', parent_container=self.container1, user=self.user1)
        self.item2 = Item.objects.create(statement='item2', parent_container=self.container2, user=self.user2)

    def test_items_filtered_correctly(self):
        # Set the token for user1
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)

        # Get the items for container1
        url = reverse('container-items', kwargs={'pk': self.container1.pk})
        response = self.client.get(url)

        # Check that the response contains only the item for user1 and container1
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.item1.id)