import torch
import torch.nn.functional as F
import time

from sentence_transformers import SentenceTransformer
from winged_app.models import CriterionVsItemsAIComparison


def all_MiniLM_L6_v2_criterion_vs_items(criterion, item_1, item_2):
    return criterion_vs_items(criterion, item_1, item_2, model_name="all-MiniLM-L6-v2")

model_name = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(model_name)

def strings_compute_criterion_embedding_comparison(criteria, item_1, item_2):
    # Convert criteria and items to embeddings
    embeddings = model.encode([criteria, item_1, item_2])

    # Normalize embeddings
    embeddings = F.normalize(torch.tensor(embeddings), p=2, dim=1)

    # Compute cosine similarity between criteria and items
    similarity_with_item_1 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
    similarity_with_item_2 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[2].unsqueeze(0))

    # Compare similarities
    return similarity_with_item_2 > similarity_with_item_1


def compute_criterion_embedding_comparison(criteria, item_1, item_2, model_name):
    model_name = "sentence-transformers/" + model_name
    model = SentenceTransformer(model_name)
    # Convert criteria and items to embeddings
    embeddings = model.encode([criteria, item_1, item_2])

    # Normalize embeddings
    embeddings = F.normalize(torch.tensor(embeddings), p=2, dim=1)

    # Compute cosine similarity between criteria and items
    similarity_with_item_1 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
    similarity_with_item_2 = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[2].unsqueeze(0))

    # Compare similarities
    return similarity_with_item_2 > similarity_with_item_1



def compute_and_store_criterion_comparison(criteria, item_1, item_2, model_name):
    start_time = time.time()
    response, item_choice = compute_criterion_embedding_comparison(
        criteria.current_criteria_statement_version.computed_statement,
        item_1.current_statement_version.statement,
        item_2.current_statement_version.statement,
        model_name,
    )
    end_time = time.time()

    if response:
        comparison = CriterionVsItemsAIComparison.objects.create(
            ai_model=model_name,
            criterion_statement_version=criteria.current_criteria_statement_version,
            item_compared_1_statement_version=item_1.current_statement_version,
            item_compared_2_statement_version=item_2.current_statement_version,
            response=response,
            item_choice=item_choice,
            execution_in_seconds=end_time - start_time
        )
        return comparison.criteria_choice

    raise ValueError("Comparison computation failed.")



def check_for_user_made_one_criterion_comparison(criterion, item_1, item_2, model_name):
    """
    Checks for a comparison the user already made from the front end
    with item's current_statement_version.
    """
    comparison = CriterionVsItemsAIComparison.objects.filter(
        user_choice=True,
        ai_model=model_name,
        criterion_statement_version=criterion.current_criteria_statement_version,
        item_compared_1_statement_version=item_1.current_statement_version,
        item_compared_2_statement_version=item_2.current_statement_version,
    )

    return comparison.order_by('created_at').reverse().first() if comparison.exists() else False



def criterion_vs_items(criterion, item_1, item_2, model_name, force_recompute=False):
    if force_recompute:
        return compute_and_store_criterion_comparison(criterion, item_1, item_2, model_name)
    
    user_made_comparison = check_for_user_made_one_criterion_comparison(criterion, item_1, item_2, model_name)
    if user_made_comparison:
        return user_made_comparison.item_choice

    try:
        comparison = CriterionVsItemsAIComparison.objects.filter(
            ai_model=model_name,
            criterion_statement_version=criterion.current_criteria_statement_version,
            item_compared_1_statement_version=item_1.current_statement_version,
            item_compared_2_statement_version=item_2.current_statement_version,
        ).order_by('created_at').reverse().first()
        if not comparison:
            raise CriterionVsItemsAIComparison.DoesNotExist
        return comparison.criteria_choice
    except CriterionVsItemsAIComparison.DoesNotExist:
        return compute_and_store_criterion_comparison(criterion, item_1, item_2, model_name)
