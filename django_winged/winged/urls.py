from django.urls import path, include
from rest_framework import routers
from winged_app.views import (
    ContainerItemListAPIView, ContainerTreeView, ContainerViewSet,
    ItemViewSet, ItemStatementVersionViewSet, UserViewSet, SpectrumValueViewSet,
    SpectrumTypeViewSet, ReEvaluateActionableItemsAPIView, CriterionVsItemsSortingScriptView,
    ItemsVsSpectrumOpeanAiComparisonCost
    )
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token

router = routers.DefaultRouter()

router.register(r'containerTrees', ContainerTreeView, basename='containerTrees')
router.register(r'containers', ContainerViewSet, basename="containers")
router.register(r'items', ItemViewSet, basename="items")
router.register(r'item_statement_versions', ItemStatementVersionViewSet, basename="itemstatementversions")
router.register(r'users', UserViewSet)
router.register(r'spectrum_type', SpectrumTypeViewSet, basename="spectrumtypes")
router.register(r'spectrum_value', SpectrumValueViewSet, basename="spectrumvalues")
#router.register(r'container_detail', ContainerDetail, basename='container_detail')


urlpatterns = [
    path('api/token/', obtain_auth_token, name='token_obtain_pair'),
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('containers/<int:pk>/items/', ContainerItemListAPIView.as_view(), name='container-items'),
    
    path("containers/<int:container_id>/criterion-vs-items-sort/criterion/<int:criterion_id>/<str:ai_model>/", CriterionVsItemsSortingScriptView.as_view(), name="criterion-vs-items-sort"),

    path('containers/<int:source_container_id>/reclassify-actionable/', ReEvaluateActionableItemsAPIView.as_view(), name='reclassify-actionable-container-items'),
    
    path('containers/<int:container_id>/spectrumtypes/<int:spectrumtype_id>/items-vs-spectrum-comparison-cost/', ItemsVsSpectrumOpeanAiComparisonCost.as_view(), name='items-vs-spectrum-comparison-cost')
]
