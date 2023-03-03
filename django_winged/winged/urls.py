from django.urls import path, include
from rest_framework import routers
from winged_app.views import ContainerItemListAPIView, ContainerTreeView, ContainerViewSet, ItemViewSet, StatementVersionViewSet, UserViewSet, SpectrumValueViewSet, SpectrumTypeViewSet
from django.contrib import admin

router = routers.DefaultRouter()

router.register(r'containerTrees', ContainerTreeView, basename='containerTrees')
router.register(r'containers', ContainerViewSet)
router.register(r'items', ItemViewSet)
router.register(r'statement_versions', StatementVersionViewSet)
router.register(r'users', UserViewSet)
router.register(r'spectrum_type', SpectrumTypeViewSet)
router.register(r'spectrum_value', SpectrumValueViewSet)
#router.register(r'container_detail', ContainerDetail, basename='container_detail')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('containers/<int:pk>/items/', ContainerItemListAPIView.as_view(), name='container-items'),
]   