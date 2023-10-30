import threading
import time
import math
import logging

from random import shuffle

from rest_framework import permissions, viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_202_ACCEPTED, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST
from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth.models import User
from django.db import transaction

from .serializers import (
    ContainerSerializer, ContainerChildrenListSerializer, ItemSerializer,
    ItemStatementVersionSerializer, UserSerializer, SpectrumTypeSerializer, 
    SpectrumValueSerializer
    )

import scripts.openai_compare as openai_compare
import scripts.ai_curation_costs_calc as costs_calc

from scripts.bart_large_mnli_compare import item_vs_criteria
from scripts.my_custom_helper_functions import reclassify_items, create_user_comparison_record, user_input_compare_criterion_vs_items
from scripts.sentence_transformers_compare import all_MiniLM_L6_v2_criterion_vs_items, strings_compute_criterion_embedding_comparison

from winged_app.models import (
    Container, Item, ItemStatementVersion, SpectrumValue, SpectrumType,
    Criteria
    )

logger = logging.getLogger('winged_app.views')

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD, or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


def log_summation(n, k):
    """
    Computes the summation of log(i) from n to n+k-1.
    
    Parameters:
    - n: Starting value of the summation.
    - k: Number of terms to sum.
    
    Returns:
    - The computed summation value.
    """
    return sum(math.log(i) for i in range(n, n+k) if i > 0)


class ItemsVsSpectrumOpeanAiComparisonCost(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, container_id, spectrumtype_id):
        try:
            spectrumtype = SpectrumType.objects.get(id=spectrumtype_id, user=self.request.user)
            container = Container.objects.get(id=container_id, user=self.request.user)
        except SpectrumType.DoesNotExist:
            return Response({"error": "SpectrumType not found"}, status=HTTP_404_NOT_FOUND)
        except Container.DoesNotExist:
            return Response({"error": "Container not found"}, status=HTTP_404_NOT_FOUND)

        #all spectrum values for this spectrum type.
        spectrum_values = SpectrumValue.objects.filter(spectrum_type=spectrumtype, user=self.request.user)
        #all spectrum values for this spectrum type that are not zero.
        non_zero_spectrum_values = spectrum_values.exclude(value=0)
        #all spectrum values for this spectrum type that are zero.
        zero_spectrum_values = spectrum_values.filter(value=0)

        #all items in this container detail -front end.
        item_list = Item.objects.filter(actionable=container.is_on_actionables_tab,
                                    archived=False,
                                    done=container.is_on_done_tab,
                                    parent_container=container,
                                    user=self.request.user
                                    )

        #all items in this container that have a spectrum value for this spectrum type that is not zero.
        scored_items_count = item_list.filter(spectrumvalue__in=non_zero_spectrum_values).count()
        #all items in this container that have a spectrum value for this spectrum type that is zero.
        zero_items_count = item_list.filter(spectrumvalue__in=zero_spectrum_values).count()
        #all items in this container that do not have a spectrum value for this spectrum type.
        new_items_count = item_list.exclude(spectrumvalue__in=spectrum_values).count()

        worst_case_comparisons = log_summation(scored_items_count, zero_items_count + new_items_count)

        tokens_in_worst_case_comparison = costs_calc.count_tokens(
            openai_compare.system_content
            + openai_compare.user_content_set_up
            + openai_compare.assistant_content
            + openai_compare.user_content
            )
        + 42*2 #worst case tokens in two items given db model lenght.
        + costs_calc.count_tokens(spectrumtype.description)

        average_output_tokens = 80 #worst case tokens in completion -upper limit from gpt4 comparisons registered.

        input_cost = 0.03 * (tokens_in_worst_case_comparison * worst_case_comparisons)
        output_cost = 0.06 * (average_output_tokens * worst_case_comparisons)

        return Response({"cost": (input_cost + output_cost)/1000})


class RunScriptAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, container_id, spectrumtype_id, comparison_mode, format=None):
        try:
            container = Container.objects.get(id=container_id, user=self.request.user)
            spectrumtype = SpectrumType.objects.get(id=spectrumtype_id, user=self.request.user)
        except Container.DoesNotExist:
            return Response({"error":f"Couldn't find Container {container_id}"}, status=HTTP_404_NOT_FOUND)
        except SpectrumType.DoesNotExist:
            return Response({"error":f"Couldn't find SpectrumType {spectrumtype_id}"}, status=HTTP_404_NOT_FOUND)
        
        sentences_to_log = [
            f"container: {container}",
            f"spectrumtype: {spectrumtype}",
            f"actionables{container.is_on_actionables_tab}",
            f"done: {container.is_on_done_tab}",
        ]

        logger.info("\n".join(sentence for sentence in sentences_to_log))

        #all spectrum values for this spectrum type.
        spectrum_values = SpectrumValue.objects.filter(spectrum_type=spectrumtype, user=self.request.user)
        #all spectrum values for this spectrum type that are not zero.
        non_zero_spectrum_values = spectrum_values.exclude(value=0)
        #all spectrum values for this spectrum type that are zero.
        zero_spectrum_values = spectrum_values.filter(value=0)

        #all items in this container's detail.
        item_list = Item.objects.filter(
            actionable=container.is_on_actionables_tab,
            archived=False,# should receive as arg from front end so right list of items is sorted.
            done=container.is_on_done_tab,# should receive as arg from front end so right list of items is sorted.
            parent_container=container,
            user=self.request.user
            )

        #all items in this container that have a spectrum value for this spectrum type that is not zero.
        scored_items = item_list.filter(spectrumvalue__in=non_zero_spectrum_values)# should be called non_zero_items instead, or even sorted items.
        #all items in this container that have a spectrum value for this spectrum type that is zero.
        zero_items = item_list.filter(spectrumvalue__in=zero_spectrum_values)
        #all items in this container that do not have a spectrum value for this spectrum type.
        new_items = item_list.exclude(spectrumvalue__in=spectrum_values)

        non_sorted_items = zero_items | new_items

        
        def run_script():# whole function can be placed elsewhere.
            def binary_insert(criteria, sorted_list, key, comparison_function):
                left, right = 0, len(sorted_list) - 1
                
                while left <= right:
                    mid = (left + right) // 2
                    
                    while True:
                        try:
                            if not comparison_function(criteria, sorted_list[mid].statement, key.statement): #why and if not? adjust that
                                left = mid + 1
                                logger.info("less than: {}".format(sorted_list[mid].statement))
                            else:
                                logger.info("more than: {}".format(sorted_list[mid].statement))
                                right = mid - 1
                            break  # do I need to exit the loop if the function call succeeded?
                        except Exception as e:  # Catch all exceptions, replace with the specific exception type if possible
                            # Wait for some time before retrying the function call
                            logger.info("Exception caught, retrying in 3 seconds", str(e))
                            time.sleep(3)
                        
                sorted_list.insert(left, key)
                return left

            def update_on_db(result):
                num_items = len(result)
                t = []#better name would help.
                for i, item in enumerate(result):
                    value = (num_items - i) * 100 // num_items

                    # get or create a SpectrumValue for the item and spectrumtype
                    spectrumvalue, created = SpectrumValue.objects.get_or_create(
                        spectrum_type=spectrumtype,
                        parent_item=item,
                        defaults={
                            'value': value,
                            'user': request.user,#can also do item.user
                        }
                    )

                    spectrumvalue.value = value#why do I pass it as default then.
                    spectrumvalue.gpt_curated = True

                    t.append(spectrumvalue)

                SpectrumValue.objects.bulk_update(t, ['value', 'gpt_curated'])

            def binary_insert_sort(criteria, items, comparison_function, sorted_list=[]):#innapropiate function name.
                total = len(items)
                j = 1# could get rid off if for loop below iterated over a range.
                shuffle(items)
                for i in items:
                    logger.info(f"inserting item {j} of {total}")
                    logger.info(f">> {i}")

                    binary_insert(criteria, sorted_list, i, comparison_function)

                    update_on_db(sorted_list)# saves one at a time to keep progress.

                    j += 1

                return sorted_list
            

            sorted_items = [i for i in scored_items.distinct()]
            sorted_items.sort(key=lambda x: x.spectrumvalue_set.get(spectrum_type=spectrumtype).value, reverse=True)
            
            functions = {
                "paraphrase-mpnet-base-v2": None,
                "all-mpnet-base-v2":strings_compute_criterion_embedding_comparison,
                "bart_large_mnli":None,
                "gpt-4":openai_compare.gpt_compare,
                "user_curation":user_input_compare_criterion_vs_items,
                }

            comparison_function = functions[comparison_mode]

            binary_insert_sort(
                spectrumtype.description,# gotta change spectrumtype model.
                [i for i in non_sorted_items.distinct()],
                comparison_function,
                sorted_list=sorted_items
                )
            
            logger.info("finished")
        
        # Start a new thread to run the script
        thread = threading.Thread(target=run_script)
        thread.start()

        return Response({"message": f"Script started for items on {container} on {spectrumtype} with {comparison_mode}."}, status=HTTP_202_ACCEPTED)


class ReEvaluateActionableItemsAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, source_container_id, format=None):
        actionable = get_object_or_404(Criteria, name="actionable", user=self.request.user)
        non_actionable = get_object_or_404(Criteria, name="non-actionable", user=self.request.user)
        source_container = get_object_or_404(Container, id=source_container_id, user=self.request.user)
        
        items = get_list_or_404(
                Item, parent_container=source_container,
                done=source_container.is_on_done_tab, archived=False, user=self.request.user
                )

        # Start a new thread to run the script
        thread = threading.Thread(
            target=reclassify_items,
            args=[items, actionable, non_actionable, item_vs_criteria]
            )
        
        thread.start()

        return Response({"message": f"Reclassifying items in {source_container_id}."}, status=HTTP_202_ACCEPTED)



class ContainerItemListAPIView(ListAPIView):
    serializer_class = ItemSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        container_id = self.kwargs.get('pk')
        return Item.objects.filter(parent_container=container_id, user=self.request.user)


class ContainerTreeView(viewsets.ViewSet):
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
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class SpectrumTypeViewSet(viewsets.ModelViewSet):
    queryset = SpectrumType.objects.all()
    serializer_class = SpectrumTypeSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            if 'actionable' in request.data:
                try:
                    create_user_comparison_record(request, instance, request.data['actionable'])
                except Exception as e:
                    transaction.set_rollback(True)
                    return Response({"error": f"An unexpected error occurred: {e}."}, status=HTTP_500_INTERNAL_SERVER_ERROR)
            return super().update(request, *args, **kwargs)


class ItemStatementVersionViewSet(viewsets.ModelViewSet):
    queryset = ItemStatementVersion.objects.all()
    serializer_class = ItemStatementVersionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
        

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
