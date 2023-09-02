from django.contrib import admin
from winged_app.models import (
    Container, Item, StatementVersion, SpectrumValue, SpectrumType,
    ItemVsTwoCriteriaAIComparison, SystemPrompt, SystemPromptTextVersion,
    Criteria, CriteriaStatementVersion)

# Register your models here.

admin.site.register(Container)
admin.site.register(Item)
admin.site.register(StatementVersion)
admin.site.register(SpectrumValue)
admin.site.register(SpectrumType)
admin.site.register(ItemVsTwoCriteriaAIComparison)
admin.site.register(SystemPrompt)
admin.site.register(SystemPromptTextVersion)
admin.site.register(Criteria)
admin.site.register(CriteriaStatementVersion)
