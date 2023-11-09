from decimal import Decimal
from django.test import TestCase, tag
from django.contrib.auth.models import User

from winged_app.models import Item, Container, Criteria, SpectrumDoublyLinkedList, SpectrumDoublyLinkedListNode


class ItemInstanceContextChangeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

        self.container_1 = Container.objects.create(name="first_user_container", user=self.user)
        self.container_2 = Container.objects.create(name="second_user_container", user=self.user)

        self.item_1 = Item.objects.create(statement=f"test_user_item_1", actionable=True, parent_container=self.container_1, user=self.user)
        self.item_2 = Item.objects.create(statement=f"test_user_item_2", actionable=True, parent_container=self.container_1, user=self.user)
        self.item_3 = Item.objects.create(statement=f"test_user_item_3", actionable=True, parent_container=self.container_1, user=self.user)

        self.criteria = Criteria.objects.create(name="test_criteria", user=self.user)

        self.head_node = SpectrumDoublyLinkedListNode.objects.create(
            data=Decimal('0.995833158493042'),
            parent_item=self.item_1,
            user=self.user
            )

        self.doubly_linked_list = SpectrumDoublyLinkedList.objects.create(
            ai_model = "all-mpnet-base-v2",
            parent_container = self.container_1,
            criterion_statement_version = self.criteria.current_criteria_statement_version,
            user=self.user,
            head=self.head_node
            )
        
        self.middle_node = SpectrumDoublyLinkedListNode.objects.create(
            data=Decimal('0.5'),
            parent_list=self.doubly_linked_list,
            parent_item=self.item_2,
            user=self.user,
            prev=self.head_node,
            )
        
        self.tail_node = SpectrumDoublyLinkedListNode.objects.create(
            data=Decimal('0.1'),
            parent_list=self.doubly_linked_list,
            parent_item=self.item_3,
            user=self.user,
            prev=self.middle_node,
            )
        
        # Give next node to head node.
        self.head_node.next = self.middle_node
        self.head_node.parent_list = self.doubly_linked_list
        self.head_node.save()

        # Give next node to middle_node.
        self.middle_node.next = self.tail_node
        self.middle_node.save()

    def assert_doubly_linked_list_start(self, dll, head, middle, tail):
        dll = SpectrumDoublyLinkedList.objects.get(pk=dll.pk)
        head = SpectrumDoublyLinkedListNode.objects.get(pk=head.pk)
        middle = SpectrumDoublyLinkedListNode.objects.get(pk=middle.pk)
        tail = SpectrumDoublyLinkedListNode.objects.get(pk=tail.pk)

        self.assertEqual(dll.head, head)
        self.assertEqual(dll.head, middle.prev)
        self.assertEqual(dll.head, tail.prev.prev)
        # Assert middle node.
        self.assertEqual(dll.head.next, head.next)
        self.assertEqual(dll.head.next, middle)
        self.assertEqual(dll.head.next, self.tail_node.prev)
        # Assert tail node.
        self.assertEqual(dll.head.next.next, head.next.next)
        self.assertEqual(dll.head.next.next, middle.next)
        self.assertEqual(dll.head.next.next, tail)

    def assert_doubly_linked_list_end(self, dll, head, middle, tail):
        dll = SpectrumDoublyLinkedList.objects.get(pk=dll.pk)
        head = SpectrumDoublyLinkedListNode.objects.get(pk=head.pk)
        tail = SpectrumDoublyLinkedListNode.objects.get(pk=tail.pk)
        
        # Assert middle_node deletion due to item context change.
        self.assertFalse(SpectrumDoublyLinkedListNode.objects.filter(pk=middle.pk).exists())

        # Assert SpectrumDoublyLinkedList relinked after middle node deletion.
        # Assert doubly-linked list head
        self.assertEqual(dll.head, head)
        self.assertEqual(dll.head, tail.prev)
        # Assert second node.
        self.assertEqual(dll.head.next, head.next)
        self.assertEqual(dll.head.next, tail)
        # Assert tail node.
        self.assertEqual(dll.head.next.next, tail.next)
        self.assertEqual(dll.head.next.next, None)


    def test_doubly_linked_list_adjustment_on_statement_change(self):
        # Assert double linked list.
        self.assert_doubly_linked_list_start(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)

        # Assert middle node's item.
        self.assertEqual(self.middle_node.parent_item, self.item_2)

        # Item context change.
        self.item_2.statement = "a different statement"
        self.item_2.save()

        # Assert double linked list changed, and previous middle node was deleted.
        self.assert_doubly_linked_list_end(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)

    
    def test_doubly_linked_list_adjustment_on_actionable_change(self):
        # Assert double linked list.
        self.assert_doubly_linked_list_start(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)

        # Assert middle node's item.
        self.assertEqual(self.middle_node.parent_item, self.item_2)

        # Item context change.
        self.item_2.actionable = not self.item_2.actionable
        self.item_2.save()

        # Assert double linked list changed, and previous middle node was deleted.
        self.assert_doubly_linked_list_end(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)


    def test_doubly_linked_list_adjustment_on_done_change(self):
        # Assert double linked list.
        self.assert_doubly_linked_list_start(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)

        # Assert middle node's item.
        self.assertEqual(self.middle_node.parent_item, self.item_2)

        # Item context change.
        self.item_2.done = not self.item_2.done
        self.item_2.save()

        # Assert double linked list changed, and previous middle node was deleted.
        self.assert_doubly_linked_list_end(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)


    def test_doubly_linked_list_adjustment_on_parent_container_change(self):
        # Assert double linked list.
        self.assert_doubly_linked_list_start(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)

        # Assert middle node's item.
        self.assertEqual(self.middle_node.parent_item, self.item_2)

        # Item context change.
        self.item_2.parent_container = self.container_2
        self.item_2.save()

        # Assert double linked list changed, and previous middle node was deleted.
        self.assert_doubly_linked_list_end(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)


    def test_doubly_linked_list_adjustment_on_archived_change(self):
        # Assert double linked list.
        self.assert_doubly_linked_list_start(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)

        # Assert middle node's item.
        self.assertEqual(self.middle_node.parent_item, self.item_2)

        # Item context change.
        self.item_2.archived = not self.item_2.archived
        self.item_2.save()

        # Assert double linked list changed, and previous middle node was deleted.
        self.assert_doubly_linked_list_end(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)


    def test_no_doubly_linked_list_adjustment_on_no_item_context_change(self):
        self.assert_doubly_linked_list_start(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)

        # Assert middle node's item.
        self.assertEqual(self.middle_node.parent_item, self.item_2)

        # Item save with no context change.
        self.item_2.save()

        self.assert_doubly_linked_list_start(self.doubly_linked_list, self.head_node, self.middle_node, self.tail_node)