from django.contrib import admin
from winged_app.models import Container, Item, StatementVersion, SpectrumValue, SpectrumType, ItemVsTwoCriteriaAIComparison

# Register your models here.

admin.site.register(Container)
admin.site.register(Item)
admin.site.register(StatementVersion)
admin.site.register(SpectrumValue)
admin.site.register(SpectrumType)
admin.site.register(ItemVsTwoCriteriaAIComparison)