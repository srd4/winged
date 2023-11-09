from django.test import TestCase

from winged_app.models import (
    Item, Container, Criteria, SpectrumDoublyLinkedListNode,
    SpectrumDoublyLinkedList, SpectrumDoublyLinkedListNode, binarily_insert_doubly_linked_list_node)

from django.contrib.auth.models import User

from math import log2


class InsertMethodTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpassword')
        
        # Create related objects
        self.container = Container.objects.create(name="Test Container", user=self.user)
        self.criteria = Criteria.objects.create(name="Test Criteria", user=self.user)
        
        item = Item.objects.create(statement="item_number_75", actionable=True, parent_container=self.container, user=self.user)
        self.head = SpectrumDoublyLinkedListNode.objects.create(parent_item=item, user=self.user)

        self.dllist = SpectrumDoublyLinkedList.objects.create(
            ai_model='TestModel',
            evaluative=False,
            parent_container=self.container,
            criterion_statement_version=self.criteria.current_criteria_statement_version,
            head=self.head,
            user=self.user
        )

        self.comparator = lambda a, b : a.parent_item.statement > b.parent_item.statement


    def test_comparator_call_count_inserting_a_node_into_a_list_of_n_sorted_nodes(self):
        expected_comparator_calls = 5
        n = (2**expected_comparator_calls)
        new_element_pos = (n + 1) // 2 + 1

        # Worst case comparison setup (need to insert element next to first middle):
        for i in range(n):
            if i == new_element_pos:
                continue
            else:
                item = Item.objects.create(statement=f"item_number_{i}", actionable=True, parent_container=self.container, user=self.user)
                self.dllist.insert(item, comparator=self.comparator)
        
        comparator_call_count = 0

        # Define a wrapper to increment counter each time the comparator is called
        def comparator_wrapper(a, b):
            nonlocal comparator_call_count
            comparator_call_count += 1
            return self.comparator(a, b)
        
        new_item = Item.objects.create(statement=f"item_number_{new_element_pos}", actionable=True, parent_container=self.container, user=self.user)
        self.dllist.insert(new_item, comparator=comparator_wrapper)

        n = SpectrumDoublyLinkedListNode.objects.filter(parent_list=self.dllist.pk).count()
        
        self.assertEqual(log2(n), comparator_call_count)
        self.assertEqual(comparator_call_count, expected_comparator_calls)


    def test_left_inserts(self):
        item_1 = Item.objects.create(statement="item_number_76", actionable=True, parent_container=self.container, user=self.user)
        self.dllist.insert(item_1, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_76")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_75")
        self.assertEqual(self.dllist.head.next.prev.parent_item.statement, "item_number_76")

        item_2 = Item.objects.create(statement="item_number_77", actionable=True, parent_container=self.container, user=self.user)
        self.dllist.insert(item_2, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_77")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_76")
        self.assertEqual(self.dllist.head.next.next.parent_item.statement, "item_number_75")

        tail = self.dllist.head.next.next

        self.assertEqual(tail.parent_item.statement, "item_number_75")
        self.assertEqual(tail.prev.parent_item.statement, "item_number_76")
        self.assertEqual(tail.prev.prev.parent_item.statement, "item_number_77")

    def test_right_inserts(self):
        item_1 = Item.objects.create(statement="item_number_50", actionable=True, parent_container=self.container, user=self.user)
        self.dllist.insert(item_1, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_75")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_50")

        item_2 = Item.objects.create(statement="item_number_0.0", actionable=True, parent_container=self.container, user=self.user)
        self.dllist.insert(item_2, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_75")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_50")
        self.assertEqual(self.dllist.head.next.next.parent_item.statement, "item_number_0.0")

        tail = self.dllist.head.next.next

        self.assertEqual(tail.parent_item.statement,"item_number_0.0")
        self.assertEqual(tail.prev.parent_item.statement, "item_number_50")
        self.assertEqual(tail.prev.prev.parent_item.statement, "item_number_75")

    def test_middle_inserts(self):
        item_1 = Item.objects.create(statement="item_number_25", actionable=True, parent_container=self.container, user=self.user)
        item_2 = Item.objects.create(statement="item_number_50", actionable=True, parent_container=self.container, user=self.user)
        self.dllist.insert(item_1, comparator=self.comparator)
        self.dllist.insert(item_2, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_75")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_50")
        self.assertEqual(self.dllist.head.next.next.parent_item.statement, "item_number_25")

        tail = self.dllist.head.next.next

        self.assertEqual(tail.parent_item.statement, "item_number_25")
        self.assertEqual(tail.prev.parent_item.statement, "item_number_50")
        self.assertEqual(tail.prev.prev.parent_item.statement, "item_number_75")

        item_3 = Item.objects.create(statement="item_number_50", actionable=True, parent_container=self.container, user=self.user)
        self.dllist.insert(item_3, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_75")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_50")
        self.assertEqual(self.dllist.head.next.next.parent_item.statement, "item_number_50")
        self.assertEqual(self.dllist.head.next.next.next.parent_item.statement, "item_number_25")

        tail = self.dllist.head.next.next.next
        
        self.assertEqual(tail.parent_item.statement, "item_number_25")
        self.assertEqual(tail.prev.parent_item.statement, "item_number_50")
        self.assertEqual(tail.prev.prev.parent_item.statement, "item_number_50")
        self.assertEqual(tail.prev.prev.prev.parent_item.statement, "item_number_75")

    def test_mixed_insertions(self):
        item_1 = Item.objects.create(statement="item_number_03", actionable=True, parent_container=self.container, user=self.user)
        item_2 = Item.objects.create(statement="item_number_71", actionable=True, parent_container=self.container, user=self.user)
        item_3 = Item.objects.create(statement="item_number_14", actionable=True, parent_container=self.container, user=self.user)
        item_4 = Item.objects.create(statement="item_number_27", actionable=True, parent_container=self.container, user=self.user)
        self.dllist.insert(item_1, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_75")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_03")

        self.dllist.insert(item_2, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_75")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_71")
        self.assertEqual(self.dllist.head.next.next.parent_item.statement, "item_number_03")

        self.dllist.insert(item_3, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_75")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_71")
        self.assertEqual(self.dllist.head.next.next.parent_item.statement, "item_number_14")
        self.assertEqual(self.dllist.head.next.next.next.parent_item.statement, "item_number_03")

        self.dllist.insert(item_4, comparator=self.comparator)

        self.assertEqual(self.dllist.head.parent_item.statement, "item_number_75")
        self.assertEqual(self.dllist.head.next.parent_item.statement, "item_number_71")
        self.assertEqual(self.dllist.head.next.next.parent_item.statement, "item_number_27")
        self.assertEqual(self.dllist.head.next.next.next.parent_item.statement, "item_number_14")
        self.assertEqual(self.dllist.head.next.next.next.next.parent_item.statement, "item_number_03")


class BinarilyInsertTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpassword')
        
        # Create related objects
        self.container = Container.objects.create(name="Test Container", user=self.user)
        self.criteria = Criteria.objects.create(name="Test Criteria", user=self.user)
        
        item = Item.objects.create(statement="item_number_2", actionable=True, parent_container=self.container, user=self.user)
        self.node2 = SpectrumDoublyLinkedListNode.objects.create(parent_item=item, user=self.user)

        self.dllist = SpectrumDoublyLinkedList.objects.create(
            ai_model='TestModel',
            evaluative=False,
            parent_container=self.container,
            criterion_statement_version=self.criteria.current_criteria_statement_version,
            head=self.node2,
            user=self.user
        )

        self.comparator = lambda a, b : a.parent_item.statement > b.parent_item.statement

    def test_correctly_inserts_to_the_left(self):
        item = Item.objects.create(statement="item_number_3", actionable=True, parent_container=self.container, user=self.user)
        node3 = SpectrumDoublyLinkedListNode.objects.create(parent_item=item, user=self.user)
        binarily_insert_doubly_linked_list_node(node3, self.dllist.head, self.comparator)

        self.assertEqual(node3.prev, None)
        self.assertEqual(node3.parent_item.statement, "item_number_3")
        self.assertEqual(node3.next.parent_item.statement, self.node2.parent_item.statement)

        self.assertEqual(self.node2.prev, node3)
        self.assertEqual(self.node2.parent_item.statement, "item_number_2")
        self.assertEqual(self.node2.next, None)
    
    def test_correctly_inserts_to_the_right(self):
        item = Item.objects.create(statement="item_number_1", actionable=True, parent_container=self.container, user=self.user)
        node1 = SpectrumDoublyLinkedListNode.objects.create(parent_item=item, user=self.user)
        binarily_insert_doubly_linked_list_node(node1, self.node2, self.comparator)

        self.assertEqual(self.node2.prev, None)
        self.assertEqual(self.node2.parent_item.statement, "item_number_2")
        self.assertEqual(self.node2.next, node1)

        self.assertEqual(node1.prev, self.node2)
        self.assertEqual(node1.parent_item.statement, "item_number_1")
        self.assertEqual(node1.next, None)

    def test_correctly_inserts_middle(self):
        item = Item.objects.create(statement="item_number_4", actionable=True, parent_container=self.container, user=self.user)
        node4 = SpectrumDoublyLinkedListNode.objects.create(parent_item=item, user=self.user)
        binarily_insert_doubly_linked_list_node(node4, self.node2, self.comparator)

        self.assertEqual(node4.prev, None)
        self.assertEqual(node4.parent_item.statement, "item_number_4")
        self.assertEqual(node4.next, self.node2)

        self.assertEqual(self.node2.prev, node4)
        self.assertEqual(self.node2.parent_item.statement, "item_number_2")
        self.assertEqual(self.node2.next, None)

        item = Item.objects.create(statement="item_number_3", actionable=True, parent_container=self.container, user=self.user)
        node3 = SpectrumDoublyLinkedListNode.objects.create(parent_item=item, user=self.user)
        binarily_insert_doubly_linked_list_node(node3, node4, self.comparator)

        self.assertEqual(node4.prev, None)
        self.assertEqual(node4.parent_item.statement, "item_number_4")
        self.assertEqual(node4.next, node3)

        self.assertEqual(node3.prev, node4)
        self.assertEqual(node3.parent_item.statement, "item_number_3")
        self.assertEqual(node3.next, self.node2)

        self.assertEqual(self.node2.prev, node3)
        self.assertEqual(self.node2.parent_item.statement, "item_number_2")
        self.assertEqual(self.node2.next, None)