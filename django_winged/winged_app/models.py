from typing import Any
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404

class Container(models.Model):
    name = models.CharField(max_length=2**6)
    description = models.TextField(max_length=2**10)
    parent_container = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_opened_at = models.DateTimeField(null=True, default=None)

    is_on_actionables_tab = models.BooleanField(default=True)
    is_on_done_tab = models.BooleanField(default=False)
    
    is_collapsed = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def update_last_opened_at(self):
        self.last_opened_at = timezone.now()
        self.save()

        return True, self.last_opened_at
    
    def toggle_tab(self):
        self.is_on_actionables_tab = not self.is_on_actionables_tab
        self.save()

        return self.is_on_actionables_tab


class Item(models.Model):
    actionable = models.BooleanField(default=False, null=False)
    done = models.BooleanField(default=False, null=False)
    statement = models.TextField(max_length=2**7)
    current_statement_version = models.ForeignKey('ItemStatementVersion', null=True, on_delete=models.SET_NULL)
    statement_updated_at = models.DateTimeField(auto_now_add=True)
    parent_container = models.ForeignKey(Container, null=True, on_delete=models.CASCADE)
    parent_item = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    archived = models.BooleanField(default=False, null=False)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def context_has_changed(self):
        """
        True if fields related to a SpectrumDoublyLinkedList's context have changed.
        """
        fields_to_check = [
            'actionable',
            'done',
            'statement',
            'current_statement_version',
            'parent_container',
            'archived',
        ]

        try:
            original = self.__class__.objects.get(pk=self.pk)
        except self.DoesNotExist:
            return (True, self)

        for field in fields_to_check:
            if getattr(self, field, None) != getattr(original, field, None):
                return (True, original)
            
        return (False, original)

    def save(self, *args, **kwargs):
        """
        Custom save method to manage current_statement_version and ItemStatementVersion.

        """
        with transaction.atomic(): # Make sure creations and saves are done in one db transaction.
            if not self.pk: # Creating instance.
                super().save(*args, **kwargs)
                self.current_statement_version = ItemStatementVersion.objects.create(statement=None, parent_item=self, user=self.user)
                self.save()
                return
            elif not self.current_statement_version:
                self.current_statement_version = ItemStatementVersion.objects.create(statement=None, parent_item=self, user=self.user)
                self.save()
            else: # Updating Instance.
                changed, original = self.context_has_changed()
                if changed:
                    for node in SpectrumDoublyLinkedListNode.objects.filter(parent_item=self.pk):
                        node.delete()
                    # Fetch self.statement as it was previous to change we are about to save.
                    if original.statement != self.statement: # Check if the statement string has been changed.
                        # Assign statement on db to current current_statement_version field.
                        self.current_statement_version.statement = original.statement
                        self.statement_updated_at = timezone.now()
                        # Save current_statement_version with old statement before droping new one.
                        self.current_statement_version.save()
                        # Drop previous current_statement_version for a new one.
                        self.current_statement_version = ItemStatementVersion.objects.create(statement=None, parent_item=self, user=self.user)

        return super().save(*args, **kwargs)


    def __str__(self):
        return self.statement

    def get_parent_container(self):
        """
        returns parent_container object as currently in db
        matters when dealing with items modified but not saved on db yet.
        """
        return get_object_or_404(Container, pk=self.parent_container.pk, user=self.user)
    
    def get_parent_item(self):
        """
        returns parent_item object as currently in db
        matters when dealing with items modified but not saved on db yet.
        """
        return get_object_or_404(Item, pk=self.parent_item.pk, user=self.user)

    def get_versions(self):
        return ItemStatementVersion.objects.filter(parent_item=self, user=self.user)

    def toggle_done(self):
        """
        Toggles the done status of the task and updates the completed_at timestamp.
        """
        self.done = not self.done
        self.completed_at = timezone.now() if self.done else None

        self.save()
        return self.done

class ItemStatementVersion(models.Model):
    """
    Statements that an element has had.
    """
    statement = models.TextField(max_length=140, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_item = models.ForeignKey(Item, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    @property
    def computed_statement(self):
        return self.statement if self.statement else self.parent_criteria.statement
    
    def __str__(self) -> str:
        return self.statement if self.statement else self.parent_item.statement

class SpectrumType(models.Model):
    name = models.CharField(max_length=2**6)
    description = models.TextField(max_length=2**9)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class SpectrumValue(models.Model):
    value = models.IntegerField()
    spectrum_type = models.ForeignKey(SpectrumType, on_delete=models.CASCADE, null=False)
    parent_item = models.ForeignKey(Item, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gpt_curated = models.BooleanField(default=False)

    class Meta:
        unique_together = ('spectrum_type', 'parent_item')

    def __str__(self) -> str:
        first_five_words = " ".join(word for word in self.parent_item.statement.split(" ")[:5])
        return f'{self.spectrum_type}: {self.value}. {first_five_words}... {self.parent_item.parent_container}.'


class ItemVsTwoCriteriaAIComparison(models.Model):
    CHOICES = [
        (True, 'Criteria 1'),
        (False, 'Criteria 2'),
    ]
    ai_model = models.CharField(max_length=2**7, null=True, db_index=True, default=None)
    user_choice = models.BooleanField(null=False, default=False)
    system_prompt_text_version = models.ForeignKey('SystemPromptTextVersion', on_delete=models.SET_NULL, null=True)
    criteria_statement_version_1 = models.ForeignKey('CriteriaStatementVersion', null=True, related_name='first_criteria_one_item_vs_two_criteria_comparisons', on_delete=models.SET_NULL, db_index=True) #if criterias are statement versions I can have access to parent Criteria on second level reference.
    criteria_statement_version_2 = models.ForeignKey('CriteriaStatementVersion', null=True, related_name='second_criteria_one_item_vs_two_criteria_comparisons', on_delete=models.SET_NULL, db_index=True)

    item_compared_statement_version = models.ForeignKey(ItemStatementVersion, related_name="one_item_vs_two_criteria_comparisons", on_delete=models.CASCADE, db_index=True)
    
    criteria_choice = models.BooleanField(choices=CHOICES, null=False, default=False, db_index=True)
    response = models.JSONField(null=True, default=None)
    execution_in_seconds = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.item_compared_statement_version.parent_item.statement

class CriterionVsItemsAIComparison(models.Model):
    CHOICES = [
        (True, 'Item 1'),
        (False, 'Item 2'),
    ]
    ai_model = models.CharField(max_length=2**7, null=True, db_index=True, default=None)
    user_choice = models.BooleanField(null=False, default=False)
    system_prompt_text_version = models.ForeignKey('SystemPromptTextVersion', on_delete=models.SET_NULL, null=True)

    criterion_statement_version = models.ForeignKey('CriteriaStatementVersion', null=True, related_name='criterion_comparisons', on_delete=models.SET_NULL, db_index=True)
    
    item_compared_1_statement_version = models.ForeignKey(ItemStatementVersion, on_delete=models.CASCADE, related_name="first_item_statement_version_criterion_comparisons", null=True)
    item_compared_2_statement_version = models.ForeignKey(ItemStatementVersion, on_delete=models.CASCADE, related_name="second_item_statement_version_criterion_comparisons", null=True)

    item_choice = models.BooleanField(choices=CHOICES, null=False, default=False, db_index=True)
    response = models.JSONField(null=True, default=None)
    execution_in_seconds = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        choice = f"{self.item_compared_1_statement_version.computed_statement if self.item_choice else self.item_compared_2_statement_version.computed_statement}"
        string = f"{self.criterion_statement_version.computed_statement} - {choice}"
        return string


class Criteria(models.Model):
    name = models.CharField(max_length=2**6)

    statement = models.CharField(max_length=2**10, null=True)
    current_criteria_statement_version = models.ForeignKey('CriteriaStatementVersion', on_delete=models.SET_NULL, null=True)

    statement_updated_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # so users can modify even default actiona vs actionable criteria statements.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Custom save method to manage current_criteria_statement_version and CriteriaStatementVersion.

        """
        with transaction.atomic(): # Make sure creations and saves are done in one db transaction.
            if not self.current_criteria_statement_version: # Creating instance.
                super().save(*args, **kwargs) # Need to save created parent_criteria first to save CriteriaStatementVersion second.
                self.current_criteria_statement_version = CriteriaStatementVersion.objects.create(statement=None, parent_criteria=self, user=self.user)
                self.save() # save above change on current_criteria_statement_version again.
                return
            elif not self.current_criteria_statement_version:
                self.current_criteria_statement_version = CriteriaStatementVersion.objects.create(statement=None, parent_criteria=self, user=self.user)
                self.save() # save above change on current_criteria_statement_version again.
                return 
            else: # Updating Instance.
                # Fetch self.statement as it was previous to change we are about to save.
                current_statement = Criteria.objects.get(pk=self.pk).statement
                if current_statement != self.statement: # Check if the statement string has been changed.
                    # Assign statement on db to current_criteria_statement_version field.
                    self.current_criteria_statement_version.statement = current_statement
                    self.statement_updated_at = timezone.now()
                    # Save current_criteria_statement_version befored droping it.
                    self.current_criteria_statement_version.save()
                    # Drop previous current_criteria_statement_version for a new one.
                    self.current_criteria_statement_version = CriteriaStatementVersion.objects.create(statement=None, parent_criteria=self, user=self.user)

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CriteriaStatementVersion(models.Model):
    statement = models.CharField(max_length=2**10, null=True)
    parent_criteria = models.ForeignKey(Criteria, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # so users can modify even default actiona vs actionable criteria statements.

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def computed_statement(self):
        return self.statement if self.statement else self.parent_criteria.statement

    def __str__(self):
        return self.statement if self.statement else self.parent_criteria.statement


class SystemPrompt(models.Model):
    name = models.CharField(max_length=2**6, unique=True)

    text = models.CharField(max_length=2**10, null=True)
    current_prompt_text_version = models.ForeignKey('SystemPromptTextVersion', null=True, on_delete=models.SET_NULL)
    prompt_text_updated_at = models.DateTimeField(auto_now_add=True)

    ai_model = models.CharField(max_length=2**7)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Custom save method to manage current_prompt_text_version and SystemPromptTextVersion.

        """
        with transaction.atomic(): # Make sure creations and saves are done in one db transaction.
            if not self.current_prompt_text_version: # Creating instance.
                super().save(*args, **kwargs) # Need to save created parent_criteria first to save SystemPromptTextVersion second.
                self.current_prompt_text_version = SystemPromptTextVersion.objects.create(text=None, parent_prompt=self, user=self.user)
                self.save() # save above change on current_prompt_text_version again.
                return
            elif not self.current_prompt_text_version:
                self.current_prompt_text_version = SystemPromptTextVersion.objects.create(text=None, parent_prompt=self, user=self.user)
                self.save() # save above change on current_prompt_text_version again.
                return
            else: # Updating Instance.
                # Fetch self.text as it was previous to change we are about to save.
                current_text = SystemPrompt.objects.get(pk=self.pk).text
                if current_text != self.text: # Check if the text string has been changed.
                    # Assign text on db to current_prompt_text_version field.
                    self.current_prompt_text_version.text = current_text
                    self.prompt_text_updated_at = timezone.now()
                    # Save current_prompt_text_version before droping it.
                    self.current_prompt_text_version.save()
                    # Drop previous current_prompt_text_version for a new one.
                    self.current_prompt_text_version = SystemPromptTextVersion.objects.create(text=None, parent_prompt=self, user=self.user)

        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.ai_model if self.ai_model else 'user'}"


class SystemPromptTextVersion(models.Model):
    text = models.CharField(max_length=2**10, null=True)
    parent_prompt = models.ForeignKey(SystemPrompt, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class SpectrumDoublyLinkedListNode(models.Model):
    parent_list = models.ForeignKey('SpectrumDoublyLinkedList', null=True, on_delete=models.CASCADE)
    parent_item = models.ForeignKey(Item, null=True, on_delete=models.CASCADE)
    data = models.DecimalField(max_digits=20, decimal_places=19, null=True)
    prev = models.ForeignKey('self', related_name="previous_node", null=True, default=None, on_delete=models.SET_NULL)
    next = models.ForeignKey('self', related_name="next_node", null=True, default=None, on_delete=models.SET_NULL)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            head, tail = self.prev, self.next
            if head:
                head.next = self.next
                self.next = None
                self.save()
                head.save()
            if tail:
                tail.prev = self.prev
                self.prev = None
                self.save()
                tail.save()
        return super().delete(*args, **kwargs)
    
    def __str__(self) -> str:
        return f"{self.data}"
    
    def __repr__(self) -> str:
        return self.__str__()


class SpectrumDoublyLinkedList(models.Model):
    CHOICES = [
        (True, 'EVALUATIVE'),
        (False, 'COMPARATIVE'),
    ]
    
    ai_model = models.CharField(max_length=2**7)
    evaluative = models.BooleanField(choices=CHOICES, null=False, default=False)
    parent_container = models.ForeignKey(Container, null=True, on_delete=models.CASCADE)
    criterion_statement_version = models.ForeignKey(CriteriaStatementVersion, null=True, on_delete=models.CASCADE)
    head = models.OneToOneField(SpectrumDoublyLinkedListNode, null=False, on_delete=models.CASCADE)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_all_items_in_container_list_context(self):
        item_list = Item.objects.filter(
            parent_container=self.parent_container,
            user=self.user,
            actionable=self.parent_container.is_on_actionables_tab,
            done=self.parent_container.is_on_done_tab,
            archived=False,# should receive as arg from front end so right list of items is sorted.
            )

        return item_list


    def get_listed_items_queryset(self, new=False):
        """
        returns context-according queryset of items.
        """
        item_list = self.get_all_container_items_in_list_context()
        
        if new:
            return item_list.exclude(spectrumdoublylinkedlistnode__in=self.get_nodes_queryset())

        return item_list.filter(spectrumdoublylinkedlistnode__in=self.get_nodes_queryset())


    def get_nodes_queryset(self):
        return SpectrumDoublyLinkedListNode.objects.filter(parent_list=self)


    def get_middle(self, head=None, end=None):
        if head == end:
            return head
        
        i, j = head, head

        while j and j.next:
            i = i.next
            j = j.next.next
            if j == end or (j and j.prev == end):
                break

        return i

    def binarily_insert(self, node, head, comparator, end=None):
        """
        (recursive) Binary insertion of a node into a doubly linked list.
        """
        if not head:
            return node
        
        middle = self.get_middle(head, end)

        if head == middle: # If head and middle are the same, the segment has only one or two nodes
            if comparator(middle, node):
                if middle.next: middle.next.prev = node
                node.next = middle.next
                middle.next = node
                node.prev = middle
                return head
            else:
                if middle.prev:middle.prev.next = node
                node.prev = middle.prev
                middle.prev = node
                node.next = middle
                return node
            
        # If head and middle differ, recursively insert the node in the appropriate segment.
        if comparator(middle, node):
            middle.next = self.binarily_insert(node, middle.next, comparator, end)
            middle.next.prev = middle
        else:
            head = self.binarily_insert(node, head, comparator, middle.prev)
        
        return head


    def insert(self, item, comparator=lambda a, b : a.data > b.data, nowait=False):
        try:
            # Select all dllist nodes for update (lock rows)
            with transaction.atomic():
                nodes = SpectrumDoublyLinkedListNode.objects.filter(parent_list=self).select_for_update(nowait=nowait)
                new_node = SpectrumDoublyLinkedListNode.objects.create(parent_list=self, parent_item=item, user=self.user)

                # Lock node rows.
                nodes.exists()
                head = self.binarily_insert(new_node, self.head, comparator)
                self.head = head.prev if head.prev else head
                self.save(update_fields=['head'])

                # Save the new node and its neighbors if they exist
                new_node.save(update_fields=['prev', 'next'])
                if new_node.next:
                    new_node.next.save(update_fields=['prev'])
                if new_node.prev:
                    new_node.prev.save(update_fields=['next'])
    
        except Exception as e:
            print("Error at SpectrumDoublyLinkedList.insert's transaction:", e)


    def __str__(self):
        strings = [str(self.head)]
        curr = self.head.next
        while curr:
            strings.append("<->")
            strings.append(str(curr))
            curr = curr.next
        return "".join(strings)

    def __repr__(self):
        return self.__str__()