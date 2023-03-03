from django.db import models
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404


"""
class ContainerGroup(models.Model):
    name = models.CharField(max_length=2**6)
    description = models.TextField(max_length=2**7, null=True)
    parent_group = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_collapsed = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    def toggle_collapsed(self):
        self.is_collapsed = not self.is_collapsed
        self.save()

        return self.is_collapsed
"""

class Container(models.Model):
    name = models.CharField(max_length=2**6)
    description = models.TextField(max_length=2**7)
    parent_container = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_opened_at = models.DateTimeField(default=timezone.now)
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
    statement_updated_at = models.DateTimeField(default=timezone.now)
    parent_container = models.ForeignKey(Container, null=True, on_delete=models.SET_NULL)
    parent_item = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(null=True, default=None)
    archived = models.BooleanField(default=False, null=False)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        """Creates StatementVersion object before saving"""
        # If the Item object already exists in the database, check if the statement field has been changed.
        if self.pk is not None:
            current_statement = Item.objects.get(pk=self.pk).statement
            if current_statement != self.statement:
                # If the statement field has been changed, create a StatementVersion object with the current statement and the statement_updated_at field as the value for the created_at field.
                StatementVersion.objects.get_or_create(
                    statement=current_statement, 
                    defaults={"created_at": self.statement_updated_at, "parent_item": self, "user": self.user}
                )

                # Set the statement_updated_at field to the current time.
                self.statement_updated_at = timezone.now()

        return super().save(*args, **kwargs)


    def __str__(self):
        return self.statement

    def get_parent_container(self):
        """returns parent_container object as currently in db"""
        return get_object_or_404(Container, pk=self.parent_container.pk, user=self.user)
    
    def get_parent_item(self):
        """returns parent_item object as currently in db"""
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
    description = models.TextField(max_length=2**7)
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

    class Meta:
        unique_together = ('spectrum_type', 'parent_item')

    def __str__(self) -> str:
        five_words = " ".join(i for i in self.parent_item.statement.split(" ")[0:5])
        return f'{self.spectrum_type}: {self.value}. {five_words}, {self.parent_item.parent_container}.'
