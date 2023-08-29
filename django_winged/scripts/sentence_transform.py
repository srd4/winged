from sentence_transformers import SentenceTransformer
import torch.nn.functional as F
import torch
import time
from winged_app.models import ItemVsTwoCriteriaAIComparison

model_name = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'

model = SentenceTransformer(model_name)

def compute_embedding_comparison(target, string_1, string_2):
    # Convert criteria and items to embeddings
    embeddings = model.encode([target, string_1, string_2])

    # Normalize embeddings
    embeddings = F.normalize(torch.tensor(embeddings), p=2, dim=1)

    # Compute cosine similarity between items and criteria
    similarity_with_string_1 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
    similarity_with_string_2 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[2].unsqueeze(0))

    # Compare similarities
    return similarity_with_string_2 < similarity_with_string_1


def item_vs_criteria(item, criteria_1, criteria_2, force_recompute=False):
    comparison, created = ItemVsTwoCriteriaAIComparison.objects.get_or_create(
        ai_model=model_name,
        criteria_1=criteria_1,
        criteria_2=criteria_2,
        item_compared=item,
    )

    if not created and not force_recompute:
        return comparison.criteria_choice

    start_time = time.time()
    comparison.criteria_choice = compute_embedding_comparison(item, criteria_1, criteria_2)
    end_time = time.time()

    comparison.execution_in_seconds = int(end_time - start_time)
    comparison.save()

    return comparison.criteria_choice

