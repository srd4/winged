from django.test import TestCase
from django.contrib.auth import get_user_model
from winged_app.models import SpectrumDoublyLinkedList, DoublyLinkedListNode, Container, Criterion

from django.contrib.auth.models import User

class SpectrumDoublyLinkedListTestCase(TestCase):

    def setUp(self):
        # Create user
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpassword')
        
        # Create related objects
        self.container = Container.objects.create(name="Test Container", user=self.user)
        self.criterion = Criterion.objects.create(name="Test Criterion", user=self.user)
        
        # Create head node
        self.head_node = DoublyLinkedListNode.objects.create(data="1", user=self.user)
        
        # Create Doubly Linked List
        self.doubly_linked_list = SpectrumDoublyLinkedList.objects.create(
            ai_model='TestModel',
            evaluative=False,
            parent_container=self.container,
            criterion_statement_version=self.criterion.current_criterion_statement_version,
            head=self.head_node,
            user=self.user
        )
        
    def test_create_doubly_linked_list(self):
        # Test that a doubly linked list can be created
        new_node = DoublyLinkedListNode.objects.create(data="1", user=self.user)

        new_list = SpectrumDoublyLinkedList.objects.create(
            ai_model='NewModel',
            evaluative=True,
            parent_container=self.container,
            criterion_statement_version=self.criterion.current_criterion_statement_version,
            head=new_node,
            user=self.user
        )
        self.assertTrue(SpectrumDoublyLinkedList.objects.filter(pk=new_list.pk).exists())

    def test_read_doubly_linked_list(self):
        # Test that a doubly linked list can be read
        fetched_list = SpectrumDoublyLinkedList.objects.get(pk=self.doubly_linked_list.pk)
        self.assertEqual(fetched_list.ai_model, 'TestModel')

    def test_update_doubly_linked_list(self):
        # Test that a doubly linked list can be updated
        self.doubly_linked_list.ai_model = 'UpdatedModel'
        self.doubly_linked_list.save()
        updated_list = SpectrumDoublyLinkedList.objects.get(pk=self.doubly_linked_list.pk)
        self.assertEqual(updated_list.ai_model, 'UpdatedModel')

    def test_delete_doubly_linked_list(self):
        # Test that a doubly linked list can be deleted
        pk = self.doubly_linked_list.pk
        self.doubly_linked_list.delete()
        self.assertFalse(SpectrumDoublyLinkedList.objects.filter(pk=pk).exists())
