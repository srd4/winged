from django.contrib.auth.models import User
from winged_app.models import Container, Item, ItemStatementVersion, SpectrumValue, SpectrumType
from rest_framework import serializers


class ContainerChildrenListSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    spectrum_types = serializers.SerializerMethodField()

    class Meta:
        model = Container
        fields = ['spectrum_types', 'id', 'name', 'description', 'parent_container', 'children', 'is_collapsed', 'is_on_actionables_tab']

    def get_children(self, container):
        children = container.container_set.exclude(parent_container=None)
        serializer = self.__class__(children, many=True)
        return serializer.data

    def get_spectrum_types(self, container):
        spectrum_types = SpectrumType.objects.filter(spectrumvalue__parent_item__parent_container=container).distinct()
        serializer = SpectrumTypeSerializer(spectrum_types, many=True)
        return serializer.data


class ItemSerializer(serializers.ModelSerializer):
    spectrum_values = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ['done', 'statement', 'id', 'parent_container','actionable', 'archived', 'spectrum_values']

    def __init__(self, *args, **kwargs):
        kwargs['partial'] = True
        super().__init__(*args, **kwargs)
    
    def create(self, validated_data):
        # set the user_id to the authenticated user
        validated_data['user_id'] = self.context['request'].user.id
        return super().create(validated_data)
    
    def get_spectrum_values(self, item):
        spectrum_values = item.spectrumvalue_set.all()
        serializer = SpectrumValueSerializer(spectrum_values, many=True)
        return serializer.data



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'



class ContainerSerializer(serializers.ModelSerializer):
    spectrum_types = serializers.SerializerMethodField()

    class Meta:
        model = Container
        fields = ['id', 'name', 'is_on_actionables_tab', 'is_collapsed', 'parent_container', 'spectrum_types']
    
    def __init__(self, *args, **kwargs):
        kwargs['partial'] = True
        super().__init__(*args, **kwargs)

    def get_spectrum_types(self, container):
        spectrum_types = SpectrumType.objects.filter(spectrumvalue__parent_item__parent_container=container).distinct()
        serializer = SpectrumTypeSerializer(spectrum_types, many=True)
        return serializer.data


class ItemStatementVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemStatementVersion
        fields = '__all__'


class SpectrumTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpectrumType
        fields = '__all__'



class SpectrumValueSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = SpectrumValue
        fields = ['id', 'value', 'spectrum_type', 'label', 'parent_item', 'gpt_curated']

    def get_label(self, spectrumvalue):
        return spectrumvalue.spectrum_type.name
    
    def create(self, validated_data):
        # set the user_id to the authenticated user
        validated_data['user_id'] = self.context['request'].user.id
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # set the user_id to the authenticated user
        validated_data['user_id'] = self.context['request'].user.id
        validated_data['gpt_curated'] = False
        return super().update(instance, validated_data)