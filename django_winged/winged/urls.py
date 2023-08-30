from django.urls import path, include
from rest_framework import routers
from winged_app.views import ContainerItemListAPIView, ContainerTreeView, ContainerViewSet, ItemViewSet, StatementVersionViewSet, UserViewSet, SpectrumValueViewSet, SpectrumTypeViewSet, RunScriptAPIView, ReclassifyContainerItemsAPIView, ReEvaluateActionableItemsAPIView
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token

router = routers.DefaultRouter()

router.register(r'containerTrees', ContainerTreeView, basename='containerTrees')
router.register(r'containers', ContainerViewSet, basename="containers")
router.register(r'items', ItemViewSet, basename="items")
router.register(r'statement_versions', StatementVersionViewSet, basename="statementversions")
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

    path("containers/<int:container_id>/run-script/spectrumtypes/<int:spectrumtype_id>/<str:comparison_mode>/", RunScriptAPIView.as_view(), name="run-script"),

    path('containers/<int:source_container_id>/reclassify/<int:container_1_id>/<int:container_2_id>/', ReclassifyContainerItemsAPIView.as_view(), name='reclassify-container-items'),

    path('containers/<int:source_container_id>/reclassify-actionable/', ReEvaluateActionableItemsAPIView.as_view(), name='reevaluate-actionable-container-items')
]
