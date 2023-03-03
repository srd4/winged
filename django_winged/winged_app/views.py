from django.contrib.auth.models import User
from winged_app.models import Container, Item, StatementVersion, SpectrumValue, SpectrumType
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import ContainerSerializer, ContainerChildrenListSerializer, ItemSerializer, StatementVersionSerializer, UserSerializer, SpectrumTypeSerializer, SpectrumValueSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.generics import ListAPIView



class ContainerItemListAPIView(ListAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        container_id = self.kwargs.get('pk')
        return Item.objects.filter(parent_container=container_id)


class ContainerTreeView(viewsets.ViewSet):
    #queryset = Container.objects.filter(parent_container=None, user=self.request.user)
    queryset = Container.objects.filter(parent_container=None)
    serializer_class = ContainerChildrenListSerializer
    #permission_classes = [permissions.IsAuthenticated]


    def list(self, request, *args, **kwargs):
        # Your list view logic here
        queryset = Container.objects.filter(parent_container=None)
        serializer = self.serializer_class(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class SpectrumValueViewSet(viewsets.ModelViewSet):
    queryset = SpectrumValue.objects.all()
    serializer_class = SpectrumValueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class SpectrumTypeViewSet(viewsets.ModelViewSet):
    queryset = SpectrumType.objects.all()
    serializer_class = SpectrumTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = []

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
        

class StatementVersionViewSet(viewsets.ModelViewSet):
    queryset = StatementVersion.objects.all()
    serializer_class = StatementVersionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
        

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]