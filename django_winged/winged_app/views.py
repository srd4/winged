from django.contrib.auth.models import User
from winged_app.models import Container, Item, StatementVersion, SpectrumValue, SpectrumType
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import ContainerSerializer, ContainerChildrenListSerializer, ItemSerializer, StatementVersionSerializer, UserSerializer, SpectrumTypeSerializer, SpectrumValueSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
import threading
import time
import scripts.openai_compare as openai_compare
from random import shuffle
from rest_framework.authentication import TokenAuthentication


def user_input_compare(criteria, element1, element2):
    response = input(f"\n1. {element1} \nvs\n2. {element2}\n(Enter 1/2): ")
    return response != "1"


class RunScriptAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, container_id, spectrumtype_id, comparison_mode, format=None):
        container = Container.objects.get(id=container_id)
        spectrumtype = SpectrumType.objects.get(id=spectrumtype_id)

        print("container: {}".format(container))
        print("spectrumtype: {}".format(spectrumtype))
        print("container.is_on_actionables_tab: {}".format(container.is_on_actionables_tab))

        #all spectrum values for this spectrum type.
        spectrum_values = SpectrumValue.objects.filter(spectrum_type=spectrumtype)
        #all spectrum values for this spectrum type that are not zero.
        non_zero_spectrum_values = spectrum_values.exclude(value=0)
        #all spectrum values for this spectrum type that are zero.
        zero_spectrum_values = spectrum_values.filter(value=0)

        #all items in this container detail -front end.
        item_list = Item.objects.filter(actionable=container.is_on_actionables_tab,
                                    archived=False,
                                    done=False,
                                    parent_container=container
                                    )

        #all items in this container that have a spectrum value for this spectrum type that is not zero.
        scored_items = item_list.filter(spectrumvalue__in=non_zero_spectrum_values)
        #all items in this container that have a spectrum value for this spectrum type that is zero.
        zero_items = item_list.filter(spectrumvalue__in=zero_spectrum_values)
        #all items in this container that do not have a spectrum value for this spectrum type.
        new_items = item_list.exclude(spectrumvalue__in=spectrum_values)

        non_sorted_items = zero_items | new_items

        def run_script():
            def binary_insert(criteria, sorted_list, key, comparison_function):
                left, right = 0, len(sorted_list) - 1
                
                while left <= right:
                    mid = (left + right) // 2
                    
                    while True:
                        try:
                            if not comparison_function(criteria, sorted_list[mid].statement, key.statement):
                                left = mid + 1
                                print("less than: {}".format(sorted_list[mid].statement))
                            else:
                                print("more than: {}".format(sorted_list[mid].statement))
                                print()
                                right = mid - 1
                            break  # Exit the loop if the function call succeeded
                        except Exception as e:  # Catch all exceptions, replace with the specific exception type if possible
                            # Wait for some time before retrying the function callz
                            print("Exception caught, retrying in 3 seconds", str(e))
                            time.sleep(3)
                        
                sorted_list.insert(left, key)
                return left

            def update_on_db(result):
                num_items = len(result)
                t = []
                for i, item in enumerate(result):
                    value = (num_items - i) * 100 // num_items

                    # get or create a SpectrumValue for the item and spectrumtype
                    spectrumvalue, created = SpectrumValue.objects.get_or_create(
                        spectrum_type=spectrumtype,
                        parent_item=item,
                        defaults={
                            'value': value,
                            'user': request.user,
                        }
                    )

                    spectrumvalue.value = value
                    spectrumvalue.gpt_curated = True

                    t.append(spectrumvalue)

                    #print("{}% - {}".format(spectrumvalue.value, spectrumvalue.parent_item)[:60])

                SpectrumValue.objects.bulk_update(t, ['value', 'gpt_curated'])

            def binary_insert_sort(criteria, items, comparison_function, sorted_list=[]):
                total = len(items)
                j = 1
                shuffle(items)
                for i in items:
                    print(f"inserting item {j} of {total}")
                    print(f">> {i}")

                    binary_insert(criteria, sorted_list, i, comparison_function)

                    update_on_db(sorted_list)

                    j += 1

                return sorted_list
            

            sorted_items = [i for i in scored_items.distinct()]
            sorted_items.sort(key=lambda x: x.spectrumvalue_set.get(spectrum_type=spectrumtype).value, reverse=True)

            if comparison_mode == "openai":
                comparison_function = openai_compare.gpt_compare
            else:
                comparison_function = user_input_compare

            result = binary_insert_sort(spectrumtype.description,
                               [i for i in non_sorted_items.distinct()],
                               comparison_function,
                               sorted_list=sorted_items)
            
            print("finished")
        
        # Start a new thread to run the script
        thread = threading.Thread(target=run_script)
        thread.start()

        return Response({"message": "Script execution started on items in container {} with spectrum type {}.".format(container_id, spectrumtype_id)})



class ContainerItemListAPIView(ListAPIView):
    serializer_class = ItemSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        container_id = self.kwargs.get('pk')
        return Item.objects.filter(parent_container=container_id).filter(user=self.request.user)


class ContainerTreeView(viewsets.ViewSet):
    queryset = Container.objects.filter(parent_container=None)
    authentication_classes = [TokenAuthentication]
    serializer_class = ContainerChildrenListSerializer
    permission_classes = [permissions.IsAuthenticated]


    def list(self, request, *args, **kwargs):
        # Your list view logic here
        queryset = Container.objects.filter(parent_container=None, user=self.request.user)
        serializer = self.serializer_class(queryset, many=True, context={"request": request})
        return Response(serializer.data)
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class SpectrumValueViewSet(viewsets.ModelViewSet):
    queryset = SpectrumValue.objects.all()
    serializer_class = SpectrumValueSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class SpectrumTypeViewSet(viewsets.ModelViewSet):
    queryset = SpectrumType.objects.all()
    serializer_class = SpectrumTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
        

class StatementVersionViewSet(viewsets.ModelViewSet):
    queryset = StatementVersion.objects.all()
    serializer_class = StatementVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
        

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

