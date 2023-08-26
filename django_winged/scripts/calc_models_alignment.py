from winged_app.models import Item, ItemVsTwoCriteriaAIComparison

def calculate_alignment_score(model1, model2, criteria_1, criteria_2):
    # Fetch paired decisions
    model1_decisions = ItemVsTwoCriteriaAIComparison.objects.filter(
        ai_model=model1, criteria_1=criteria_1, criteria_2=criteria_2
    ).values('item_compared', 'criteria_choice')

    model2_decisions = ItemVsTwoCriteriaAIComparison.objects.filter(
        ai_model=model2, criteria_1=criteria_1, criteria_2=criteria_2
    ).values('item_compared', 'criteria_choice')

    model1_dict = {d['item_compared']: d['criteria_choice'] for d in model1_decisions}
    model2_dict = {d['item_compared']: d['criteria_choice'] for d in model2_decisions}

    # Calculate matches
    matching_decisions = sum(
        model1_dict[item] == model2_dict[item] 
        for item in model1_dict 
        if item in model2_dict
    )

    # Calculate total
    total_decisions = len(model1_dict)

    # Calculate alignment score
    alignment_score = (matching_decisions/total_decisions) * 100

    return alignment_score



def find_disalignments(model1, model2, criteria_1, criteria_2):
    # Fetch paired decisions
    model1_decisions = ItemVsTwoCriteriaAIComparison.objects.filter(
        ai_model=model1, criteria_1=criteria_1, criteria_2=criteria_2
    ).values('item_compared', 'criteria_choice')

    model2_decisions = ItemVsTwoCriteriaAIComparison.objects.filter(
        ai_model=model2, criteria_1=criteria_1, criteria_2=criteria_2
    ).values('item_compared', 'criteria_choice')

    model1_dict = {d['item_compared']: d['criteria_choice'] for d in model1_decisions}
    model2_dict = {d['item_compared']: d['criteria_choice'] for d in model2_decisions}

    # Find disalignments
    disalignments = [
        item for item in model1_dict 
        if item in model2_dict and model1_dict[item] != model2_dict[item]
    ]

    return disalignments



def run():
    actionable = "Actionable: Tasks directly affecting external output. Example: 'Code Django feature.'"
    non_actionable = "Non-Actionable: Tasks mainly affecting internal thought processes. Example: 'Watch lecture for insight.'"

    print("The alignment score is: ", calculate_alignment_score('gpt-4', 'SentenceTransformer', actionable, non_actionable))

