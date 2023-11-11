import time
import requests
import os
import logging

from requests.exceptions import Timeout, RequestException

from winged_app.models import ItemVsTwoCriteriaAIComparison

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
class HuggingFaceZeroShotAPIError(Exception):
    pass

class HuggingFaceZeroShotAPITimeoutError(HuggingFaceZeroShotAPIError):
    pass

class HuggingFaceZeroShotAPIInvalidResponse(HuggingFaceZeroShotAPIError):
    pass

logger = logging.getLogger('scripts.bart_large_mnli_compare')

def api_call(url, headers, data):
    response = None
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        logger.info(f"API response: {response.status_code}, {response.text}")
        return response
    except Timeout as e:
        logger.error(f"Timeout error: {e}")
        if response:
            logger.info(f"API response: {response.status_code}, {response.text}")
        raise HuggingFaceZeroShotAPITimeoutError()
    except RequestException as e:
        logger.error(f"Request exception: {e}")
        if response:
            logger.info(f"API response: {response.status_code}, {response.text}")
        raise HuggingFaceZeroShotAPIError()


def parse_response(response, criterion_version_1_statement):
    json_response = response.json()
    if 'labels' not in json_response:
        logger.error("Invalid response: 'labels' missing")
        raise HuggingFaceZeroShotAPIInvalidResponse("Invalid response: 'labels' missing") from None
    return json_response, json_response['labels'][0] == criterion_version_1_statement


#this function can be generalized to be used with criterion vs two item statements too.
def compute_zero_shot_comparison(item_statement_version_statement, criterion_version_1_statement, criterion_version_2_statement, api_key=HUGGINGFACE_API_KEY, api_url=API_URL, post_function=api_call, parser_function=parse_response):
    remaining_attempts = 3
    sleep_time = 5

    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"inputs": item_statement_version_statement, "parameters": {"candidate_labels": [criterion_version_1_statement, criterion_version_2_statement]}}

    while remaining_attempts > 0:
        try:
            time.sleep(sleep_time)
            response = post_function(api_url, headers, data)
            result = parser_function(response, criterion_version_1_statement)
            return result
            
        except HuggingFaceZeroShotAPITimeoutError:
            logger.warning("Timeout occurred, retrying...")
            remaining_attempts -= 1
            continue
        
        except HuggingFaceZeroShotAPIError:
            logger.warning("API error occurred, retrying with increased sleep time...")
            remaining_attempts -= 1
            sleep_time *= 2
            continue
        

    logger.error("Max retries reached without successful API response.")
    raise HuggingFaceZeroShotAPIError("Max retries reached without successful API response.")



def check_for_user_made_comparison(item, criterion_1, criterion_2):
    """
    Checks for a comparison the user already made from the front end
    with item's current_statement_version.
    """
    comparison = ItemVsTwoCriteriaAIComparison.objects.filter(
        user_choice=True,
        criterion_statement_version_1=criterion_1.current_criterion_statement_version,
        criterion_statement_version_2=criterion_2.current_criterion_statement_version,
        item_compared_statement_version=item.current_statement_version,
    )

    return comparison.order_by('created_at').reverse().first() if comparison.exists() else False



def item_vs_criteria(item, criterion_1, criterion_2, force_recompute=False):
    if force_recompute:
        return compute_and_store_comparison(item, criterion_1, criterion_2)
    
    user_made_comparison = check_for_user_made_comparison(item, criterion_1, criterion_2)
    if user_made_comparison:
        return user_made_comparison.criterion_choice

    try:
        comparison = ItemVsTwoCriteriaAIComparison.objects.filter(
            ai_model="bart-large-mnli",
            criterion_statement_version_1=criterion_1.current_criterion_statement_version,
            criterion_statement_version_2=criterion_1.current_criterion_statement_version,
            item_compared_statement_version=item.current_statement_version,
        ).order_by('created_at').reverse().first()
        if not comparison:
            raise ItemVsTwoCriteriaAIComparison.DoesNotExist
        return comparison.criterion_choice
    except ItemVsTwoCriteriaAIComparison.DoesNotExist:
        return compute_and_store_comparison(item, criterion_1, criterion_2)



def compute_and_store_comparison(item, criterion_1, criterion_2):
    start_time = time.time()
    response, criterion_choice = compute_zero_shot_comparison(
        item.current_statement_version.parent_item.statement,
        criterion_1.current_criterion_statement_version.computed_statement,
        criterion_2.current_criterion_statement_version.computed_statement,
    )
    end_time = time.time()

    if response:
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model="bart-large-mnli",
            criterion_statement_version_1=criterion_1.current_criterion_statement_version,
            criterion_statement_version_2=criterion_2.current_criterion_statement_version,
            item_compared_statement_version=item.current_statement_version,
            response=response,
            criterion_choice=criterion_choice,
            execution_in_seconds=end_time - start_time
        )
        return comparison.criterion_choice

    raise ValueError("Comparison computation failed.")
