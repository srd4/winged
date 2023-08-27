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

    models = [
        "sentence-transformers/msmarco-MiniLM-L12-cos-v5",
        "sentence-transformers/msmarco-distilbert-multilingual-en-de-v2-tmp-trained-scratch",
        "sentence-transformers/msmarco-distilroberta-base-v2",
        "sentence-transformers/msmarco-distilbert-base-v2",
        "sentence-transformers/msmarco-distilbert-multilingual-en-de-v2-tmp-lng-aligned",
        "sentence-transformers/msmarco-MiniLM-L-12-v3",
        "sentence-transformers/msmarco-MiniLM-L-6-v3",
        "sentence-transformers/msmarco-distilbert-base-v3",
        "sentence-transformers/msmarco-distilbert-cos-v5",
        "sentence-transformers/msmarco-distilbert-base-dot-prod-v3",
        "sentence-transformers/msmarco-distilbert-dot-v5",
        "sentence-transformers/msmarco-distilbert-base-v4",
        "sentence-transformers/msmarco-MiniLM-L6-cos-v5",
        "sentence-transformers/msmarco-distilbert-base-tas-b",
        "sentence-transformers/paraphrase-albert-base-v2",
        "sentence-transformers/paraphrase-albert-small-v2",
        "sentence-transformers/paraphrase-MiniLM-L12-v2",
        "sentence-transformers/paraphrase-MiniLM-L3-v2",
        "sentence-transformers/paraphrase-MiniLM-L6-v2",
        "sentence-transformers/paraphrase-TinyBERT-L6-v2",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "sentence-transformers/xlm-r-distilroberta-base-paraphrase-v1",
        "sentence-transformers/paraphrase-distilroberta-base-v2",
        "sentence-transformers/paraphrase-distilroberta-base-v1",
        "sentence-transformers/paraphrase-xlm-r-multilingual-v1",
        "sentence-transformers/paraphrase-mpnet-base-v2",
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "sentence-transformers/msmarco-bert-co-condensor",
        "sentence-transformers/msmarco-roberta-base-ance-firstp",
        "sentence-transformers/msmarco-roberta-base-v2",
        "sentence-transformers/msmarco-roberta-base-v3",
        "sentence-transformers/msmarco-bert-base-dot-v5",
    ]
    
    for i in models:
        print(f"The alignment score of 'gpt-4' with {i} is: ", calculate_alignment_score('gpt-4', i, actionable, non_actionable))




"""
The alignment score of gpt-4 with gpt-3.5-turbo is:  79.375

The alignment score of 'gpt-4' with sentence-transformers/msmarco-MiniLM-L12-cos-v5 is:  68.75
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilbert-multilingual-en-de-v2-tmp-trained-scratch is:  51.24999999999999
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilroberta-base-v2 is:  66.875
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilbert-base-v2 is:  73.125
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilbert-multilingual-en-de-v2-tmp-lng-aligned is:  70.0
The alignment score of 'gpt-4' with sentence-transformers/msmarco-MiniLM-L-12-v3 is:  68.75
The alignment score of 'gpt-4' with sentence-transformers/msmarco-MiniLM-L-6-v3 is:  65.625
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilbert-base-v3 is:  70.625
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilbert-cos-v5 is:  77.5
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilbert-base-dot-prod-v3 is:  74.375
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilbert-dot-v5 is:  67.5
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilbert-base-v4 is:  77.5
The alignment score of 'gpt-4' with sentence-transformers/msmarco-MiniLM-L6-cos-v5 is:  65.625
The alignment score of 'gpt-4' with sentence-transformers/msmarco-distilbert-base-tas-b is:  73.75
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-albert-base-v2 is:  72.5
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-albert-small-v2 is:  75.625
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-MiniLM-L12-v2 is:  75.625
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-MiniLM-L3-v2 is:  71.875
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-MiniLM-L6-v2 is:  65.625
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-TinyBERT-L6-v2 is:  76.875
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 is:  74.375
The alignment score of 'gpt-4' with sentence-transformers/xlm-r-distilroberta-base-paraphrase-v1 is:  75.625
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-distilroberta-base-v2 is:  76.875
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-distilroberta-base-v1 is:  73.125
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-xlm-r-multilingual-v1 is:  75.625
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-mpnet-base-v2 is:  83.125
The alignment score of 'gpt-4' with sentence-transformers/paraphrase-multilingual-mpnet-base-v2 is:  81.875
The alignment score of 'gpt-4' with sentence-transformers/msmarco-bert-co-condensor is:  81.875
The alignment score of 'gpt-4' with sentence-transformers/msmarco-roberta-base-ance-firstp is:  77.5
The alignment score of 'gpt-4' with sentence-transformers/msmarco-roberta-base-v2 is:  71.25
The alignment score of 'gpt-4' with sentence-transformers/msmarco-roberta-base-v3 is:  61.875
The alignment score of 'gpt-4' with sentence-transformers/msmarco-bert-base-dot-v5 is:  80.0


The alignment score of gpt-3.5-turbo with sentence-transformers/distiluse-base-multilingual-cased-v1 is:  65.0
The alignment score of gpt-3.5-turbo with sentence-transformers/paraphrase-MiniLM-L3-v2 is:  61.25000000000001
The alignment score of gpt-3.5-turbo with sentence-transformers/paraphrase-mpnet-base-v2 is:  75.0
The alignment score of gpt-3.5-turbo with sentence-transformers/LaBSE is:  64.375
The alignment score of gpt-3.5-turbo with sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens is:  72.5
The alignment score of gpt-3.5-turbo with sentence-transformers/distilbert-base-nli-mean-tokens is:  66.875
The alignment score of gpt-3.5-turbo with sentence-transformers/msmarco-bert-base-dot-v5 is:  69.375
The alignment score of gpt-3.5-turbo with sentence-transformers/multi-qa-MiniLM-L6-cos-v1 is:  65.625
The alignment score of gpt-3.5-turbo with sentence-transformers/multi-qa-mpnet-base-dot-v1 is:  70.0
The alignment score of gpt-3.5-turbo with sentence-transformers/distiluse-base-multilingual-cased-v2 is:  64.375
"""

