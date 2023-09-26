from winged_app.models import Item, Criteria
from scripts.bart_large_mnli_compare import item_vs_criteria


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