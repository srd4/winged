import time
import requests
import os
import logging

from requests.exceptions import Timeout, RequestException
from json.decoder import JSONDecodeError

from winged_app.models import ItemVsTwoCriteriaAIComparison

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
class HuggingFaceZeroShotAPIError(Exception):
    pass

class HuggingFaceZeroShotAPITimeoutError(HuggingFaceZeroShotAPIError):
    pass

class HuggingFaceZeroShotAPIInvalidResponse(HuggingFaceZeroShotAPIError):
    pass

logging.basicConfig(filename='api_logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def api_call(url, headers, data):
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        logging.info(f"API response: {response.status_code}, {response.text}")
        return response
    except Timeout as e:
        logging.error(f"Timeout error: {e}")
        if response:
            logging.info(f"API response: {response.status_code}, {response.text}")
        raise HuggingFaceZeroShotAPITimeoutError()
    except RequestException as e:
        logging.error(f"Request exception: {e}")
        if response:
            logging.info(f"API response: {response.status_code}, {response.text}")
        raise HuggingFaceZeroShotAPIError()


def parse_response(response, criteria__version_1_statement):
    json_response = response.json()
    if 'labels' not in json_response:
        logging.error("Invalid response: 'labels' missing")
        raise HuggingFaceZeroShotAPIInvalidResponse("Invalid response: 'labels' missing") from None
    return json_response, json_response['labels'][0] == criteria__version_1_statement


#this function can be generalized to be used with criterion vs two item statements too.
def compute_zero_shot_comparison(item_statement_version_statement, criteria__version_1_statement, criteria_version_2_statement, api_key=HUGGINGFACE_API_KEY, api_url=API_URL, post_function=api_call, parser_function=parse_response):
    remaining_attempts = 3
    sleep_time = 5

    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"inputs": item_statement_version_statement, "parameters": {"candidate_labels": [criteria__version_1_statement, criteria_version_2_statement]}}

    while remaining_attempts > 0:
        try:
            time.sleep(sleep_time)
            response = post_function(api_url, headers, data)
            result = parser_function(response, criteria__version_1_statement)
            return result
            
        except HuggingFaceZeroShotAPITimeoutError:
            logging.warning("Timeout occurred, retrying...")
            remaining_attempts -= 1
            continue
        
        except HuggingFaceZeroShotAPIError:
            logging.warning("API error occurred, retrying with increased sleep time...")
            remaining_attempts -= 1
            sleep_time *= 2
            continue
        

    logging.error("Max retries reached without successful API response.")
    raise HuggingFaceZeroShotAPIError("Max retries reached without successful API response.")



def check_for_user_made_comparison(item, criteria_1, criteria_2):
    """
    Checks for a comparison the user already made from the front end
    with item's current_statement_version.
    """
    comparison = ItemVsTwoCriteriaAIComparison.objects.filter(
        user_choice=True,
        criteria_1=criteria_1.current_criteria_statement_version,
        criteria_2=criteria_2.current_criteria_statement_version,
        item_compared_statement_version=item.current_statement_version,
    )

    return comparison.order_by('created_at').reverse().first() if comparison.exists() else False



def item_vs_criteria(item, criteria_1, criteria_2, force_recompute=False):
    if force_recompute:
        return compute_and_store_comparison(item, criteria_1, criteria_2)
    
    user_made_comparison = check_for_user_made_comparison(item, criteria_1, criteria_2)
    if user_made_comparison:
        return user_made_comparison.criteria_choice

    try:
        comparison = ItemVsTwoCriteriaAIComparison.objects.filter(
            ai_model="bart-large-mnli",
            criteria_statement_version_1=criteria_1.current_criteria_statement_version,
            criteria_statement_version_2=criteria_2.current_criteria_statement_version,
            item_compared_statement_version=item.current_statement_version,
        ).order_by('created_at').reverse().first()
        if not comparison:
            raise ItemVsTwoCriteriaAIComparison.DoesNotExist
        return comparison.criteria_choice
    except ItemVsTwoCriteriaAIComparison.DoesNotExist:
        return compute_and_store_comparison(item, criteria_1, criteria_2)


def compute_and_store_comparison(item, criteria_1, criteria_2):
    start_time = time.time()
    response, criteria_choice = compute_zero_shot_comparison(
        item.current_statement_version.parent_item.statement,
        criteria_1.current_criteria_statement_version.computed_statement,
        criteria_2.current_criteria_statement_version.computed_statement,
    )
    end_time = time.time()

    if response:
        comparison = ItemVsTwoCriteriaAIComparison.objects.create(
            ai_model="bart-large-mnli",
            criteria_statement_version_1=criteria_1.current_criteria_statement_version,
            criteria_statement_version_2=criteria_2.current_criteria_statement_version,
            item_compared_statement_version=item.current_statement_version,
            response=response,
            criteria_choice=criteria_choice,
            execution_in_seconds=end_time - start_time
        )
        return comparison.criteria_choice

    raise ValueError("Comparison computation failed.")
