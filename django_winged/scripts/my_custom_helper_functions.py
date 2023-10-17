from django.shortcuts import get_object_or_404
from winged_app.models import Item, Criteria, ItemVsTwoCriteriaAIComparison
from scripts.bart_large_mnli_compare import item_vs_criteria


"""
            criteria_1=criteria_1.current_criteria_statement_version,
            criteria_2=criteria_2.current_criteria_statement_version,
            item_compared_statement_version=item.current_statement_version,
            """


def create_user_comparison_record(request, item, actionable):
    actionable_criteria = get_object_or_404(Criteria, name="actionable", user=request.user)
    non_actionable_criteria = get_object_or_404(Criteria, name="non-actionable", user=request.user)

    comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            user_choice=True,
            criteria_statement_version_1=actionable_criteria.current_criteria_statement_version,
            criteria_statement_version_2=non_actionable_criteria.current_criteria_statement_version,
            item_compared_statement_version=item.current_statement_version,
            criteria_choice=actionable,
        )
    return comparison


def reclassify_items(items, criteria_1, criteria_2, comparison_function):
    total = len(items)
    count = 0
    
    for item in items:
        count += 1
        try:
            result = comparison_function(item, criteria_1, criteria_2)
        except Exception as e: # make sure result is either valid or raise an exception on comparison_function.
            fail_message = f"{item.pk}|'{' '.join(item.statement.split(' ')[0:5])}...' failed to be processed. {e}"
            print(fail_message)
            continue
        
        item.actionable = result
        item.save()

        success_message = f"{count}/{total} processed. '{item}'\nsent to {'actionable' if result else 'non-actionable'}."
        
        print(success_message)


def run():
    """
    with "py manage.py runscript my_custom_helper_functions" to
    run reclassify_items over all items in db.
    """
    items = Item.objects.all()
    actionable = Criteria.objects.get(name="actionable")
    non_actionable = Criteria.objects.get(name="non-actionable")

    reclassify_items(items, actionable, non_actionable, item_vs_criteria)


def user_input_compare_criterion_vs_items(criteria, element1, element2):
    response = input(f"\n1. {element1} \nvs\n2. {element2}\n(Enter 1/2): ")
    return response != "1"