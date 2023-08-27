from sentence_transformers import SentenceTransformer
import torch.nn.functional as F
import torch
import time
from winged_app.models import ItemVsTwoCriteriaAIComparison, Container, Item

def run():
    """suggested_models = [
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
    ]"""

    suggested_models = [
        "sentence-transformers/all-mpnet-base-v2",
        "sentence-transformers/all-distilroberta-v1",
        "sentence-transformers/all-MiniLM-L12-v2",
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/multi-qa-mpnet-base-dot-v1",
        "sentence-transformers/multi-qa-distilbert-cos-v1",
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "sentence-transformers/paraphrase-albert-small-v2",
        "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "sentence-transformers/paraphrase-MiniLM-L3-v2",
        "sentence-transformers/distiluse-base-multilingual-cased-v1",
        "sentence-transformers/distiluse-base-multilingual-cased-v2",
    ]

    for model_name in suggested_models:
        try:
            model = SentenceTransformer(model_name)
            c = Container.objects.get(name="myself")
            t = Item.objects.filter(parent_container=c, done=False, archived=False)
            reclassify_items(t, model, model_name)
        except:
            continue


def embedding_compare(model, criteria, item_1, item_2):
    embeddings = model.encode([criteria, item_1, item_2])
    embeddings = F.normalize(torch.tensor(embeddings), p=2, dim=1)
    sim1 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
    sim2 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[2].unsqueeze(0))
    return sim2 > sim1

def compute_embedding_comparison(model, item, criteria_1, criteria_2):
    embeddings = model.encode([item, criteria_1, criteria_2])
    embeddings = F.normalize(torch.tensor(embeddings), p=2, dim=1)
    sim1 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
    sim2 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[2].unsqueeze(0))
    return sim2 < sim1

def item_vs_criteria(model, item, criteria_1, criteria_2, model_name, force_recompute=False):
    comparison, created = ItemVsTwoCriteriaAIComparison.objects.get_or_create(
        ai_model=model_name,
        criteria_1=criteria_1,
        criteria_2=criteria_2,
        item_compared=item,
    )
    if not created and not force_recompute:
        return comparison.criteria_choice

    start_time = time.time()
    comparison.criteria_choice = compute_embedding_comparison(model, item, criteria_1, criteria_2)
    end_time = time.time()
    comparison.execution_in_seconds = int(end_time - start_time)
    comparison.save()

    return comparison.criteria_choice

def reclassify_items(items, model, model_name):
    actionable = "Actionable: Tasks directly affecting external output. Example: 'Code Django feature.'"
    non_actionable = "Non-Actionable: Tasks mainly affecting internal thought processes. Example: 'Watch lecture for insight.'"
    
    total = len(items)
    count = 0
    for item in items:
        for _ in range(5):
            try:
                result = item_vs_criteria(model, item, actionable, non_actionable, model_name)
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                continue
        else:
            print("Failed after 3 attempts.")
        
        item.actionable = result
        item.save()
        count += 1
        print(f"{count}/{total}.{item} \n sent to {'actionable' if result else 'non-actionable'}")
