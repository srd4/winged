from django.db import models
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
    statement_updated_at = models.DateTimeField(auto_now_add=True)
    parent_container = models.ForeignKey(Container, null=True, on_delete=models.CASCADE)
    parent_item = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(null=True, default=None)
    archived = models.BooleanField(default=False, null=False)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        """
        Creates StatementVersion object before saving
        """

        # If the Item object already exists on db...
        if self.pk is not None:
            current_statement = Item.objects.get(pk=self.pk).statement
            # ...check if the statement field has been changed.
            if current_statement != self.statement:
                # If the statement field has been changed, create a StatementVersion object with
                # the statement on db.
                StatementVersion.objects.get_or_create(
                    statement=current_statement, 
                    defaults={
                        "created_at": self.statement_updated_at,
                        "parent_item": self,
                        "user": self.user
                        }
                )

                # Set statement_updated_at attribute to the current time.
                self.statement_updated_at = timezone.now()

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
        return StatementVersion.objects.filter(parent_item=self, user=self.user)

    def toggle_done(self):
        """
        Toggles the done status of the task and updates the completed_at timestamp.
        """
        self.done = not self.done
        self.completed_at = timezone.now() if self.done else None

        self.save()
        return self.done



class StatementVersion(models.Model):
    """
    Statements that an element has had.
    """
    statement = models.TextField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_item = models.ForeignKey(Item, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.statement


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
    ai_model = models.CharField(max_length=2**7, db_index=True)
    system_prompt = models.ForeignKey('SystemPromptTextVersion', on_delete=models.SET_NULL, null=True)
    criteria_1 = models.ForeignKey('CriteriaStatementVersion', null=True, related_name='criteria_1', on_delete=models.SET_NULL, db_index=True) #if criterias are statement versions I can have access to parent Criteria on second level reference.
    criteria_2 = models.ForeignKey('CriteriaStatementVersion', null=True, related_name='criteria_2', on_delete=models.SET_NULL, db_index=True)
    item_compared = models.ForeignKey(Item, on_delete=models.CASCADE, db_index=True)
    criteria_choice = models.BooleanField(choices=CHOICES, null=False, default=False, db_index=True)
    response = models.JSONField(null=True, default=None)
    execution_in_seconds = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_compared.statement} - {self.ai_model}"


class Criteria(models.Model):
    name = models.CharField(max_length=2**6)
    criteria_statement_version = models.ForeignKey('CriteriaStatementVersion', on_delete=models.SET_NULL, null=True)
    statement_updated_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # so users can modify even default actiona vs actionable criteria statements.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CriteriaStatementVersion(models.Model):
    statement = models.CharField(max_length=2**10)
    parent_criteria = models.ForeignKey(Criteria, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # so users can modify even default actiona vs actionable criteria statements.

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        
        if self.parent_criteria:
            self.parent_criteria.criteria_statement_version = self
            self.parent_criteria.save()

    def __str__(self):
        return self.statement


class SystemPrompt(models.Model):
    name = models.CharField(max_length=2**6, unique=True)
    prompt_text_version = models.ForeignKey('SystemPromptTextVersion', null=True, on_delete=models.SET_NULL)
    ai_model = models.CharField(max_length=2**7)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.ai_model}"


class SystemPromptTextVersion(models.Model):
    text = models.CharField(max_length=2**10)
    parent_prompt = models.ForeignKey(SystemPrompt, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)

        if self.parent_prompt:
            self.parent_prompt.prompt_text_version = self
            self.parent_prompt.save()

    def __str__(self):
        return self.prompt_text