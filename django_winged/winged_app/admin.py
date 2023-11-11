from django.contrib import admin
from winged_app.models import (
    Container, Item, ItemStatementVersion, SpectrumValue, SpectrumType,
    ItemVsTwoCriteriaAIComparison, SystemPrompt, SystemPromptTextVersion,
    Criterion, CriterionStatementVersion)

# Register your models here.

admin.site.register(Container)
admin.site.register(Item)
admin.site.register(ItemStatementVersion)
admin.site.register(SpectrumValue)
admin.site.register(SpectrumType)
admin.site.register(ItemVsTwoCriteriaAIComparison)
admin.site.register(SystemPrompt)
admin.site.register(SystemPromptTextVersion)
admin.site.register(Criterion)
admin.site.register(CriterionStatementVersion)
