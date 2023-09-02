import time
from winged_app.models import Item, Criteria
from bart_large_mnli_compare import item_vs_criteria

PERCENTAGE_CHUNK = 20  # 10% of total items as a chunk

def reclassify_items(items, criteria_1, criteria_2, comparison_function):
    total = len(items)
    chunk_size = max(1, (total * PERCENTAGE_CHUNK) // 100)  # At least one item per chunk
    count = 0
    updated_items = []
    
    for item in items:
        try:
            result = comparison_function(item, criteria_1, criteria_2)
        except Exception as e:
            print(f"An error occurred classifying item {item.pk}: {e}")
            continue
        
        item.actionable = result
        updated_items.append(item)
        count += 1
        print(f"{count}/{total} processed. '{item}' \nsent to {'actionable' if result else 'non-actionable'}.")

        # Update in chunks based on percentage
        if len(updated_items) >= chunk_size:
            Item.objects.bulk_update(updated_items, ['actionable'])
            updated_items = []

    # Update any remaining items
    if updated_items:
        Item.objects.bulk_update(updated_items, ['actionable'])


def run():
    items = Item.objects.all()
    actionable = Criteria.objects.get(name="actionable")
    non_actionable = Criteria.objects.get(name="non-actionable")

    reclassify_items(items, actionable, non_actionable, item_vs_criteria)