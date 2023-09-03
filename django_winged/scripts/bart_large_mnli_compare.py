import time
import requests
import os

from requests.exceptions import Timeout, RequestException
from json.decoder import JSONDecodeError

from winged_app.models import ItemVsTwoCriteriaAIComparison



HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"


def compute_zero_shot_comparison(item_statement, criteria_1_statement, criteria_2_statement):
    remaining_attempts = 5
    sleep_time = 5

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    data = {"inputs": item_statement, "parameters": {"candidate_labels": [criteria_1_statement, criteria_2_statement]}}

    while remaining_attempts > 0:
        try:
            time.sleep(sleep_time)
            response = requests.post(API_URL, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
        except Timeout:
            print("Timeout occurred.", response.content if 'response' in locals() else "")
            remaining_attempts -= 1
            continue
        
        except RequestException as e:
            if 'response' in locals() and response.status_code == 429:  # Rate-limited
                print(f"Hit rate limit. Trying again in {sleep_time * 2} seconds...")
                sleep_time *= 2
            elif 'response' in locals() and response.status_code == 503:  # Service unavailable
                print("Service unavailable. Trying again...", response.content if 'response' in locals() else "")
            remaining_attempts -= 1
            continue
        
        try:
            response_json = response.json()
            if 'labels' not in response_json:
                raise ValueError("Invalid response: 'labels' missing") from None
            return response_json, response_json['labels'][0] == criteria_1_statement
        
        except JSONDecodeError as e:
            print(f"JSON decode error occurred: {e}", response.content if 'response' in locals() else "")
            remaining_attempts -= 1
            continue
        except Exception as e:
            remaining_attempts -= 1
            print(f"An unknown error occurred: {e}", response.content if 'response' in locals() else "")
            continue

    raise ValueError("Coudln't bring choice to a valid value.")

        

def item_vs_criteria(item, criteria_1, criteria_2, force_recompute=False):
    created_here = False

    try:
        # Get comparison if already made to avoid re-computing it.
        comparison = ItemVsTwoCriteriaAIComparison.objects.get(
            ai_model="bart-large-mnli",
            criteria_1=criteria_1.statement_version,
            criteria_2=criteria_2.statement_version,
            item_compared=item)
        
    except ItemVsTwoCriteriaAIComparison.DoesNotExist:
        # Create comparison if not already made.
        created_here = True
        comparison = ItemVsTwoCriteriaAIComparison(
            ai_model="bart-large-mnli",
            criteria_1=criteria_1.statement_version,
            criteria_2=criteria_2.statement_version,
            item_compared=item
            )

    
    if not created_here and not force_recompute:
        # Return already computed choice if comparison already exists and computation is not being forced.
        return comparison.criteria_choice
    

    start_time = time.time()

    comparison.response, comparison.criteria_choice,  = compute_zero_shot_comparison(
        item.statement,
        criteria_1.statement_version.statement, # sent strint
        criteria_2.statement_version.statement,
    )

    end_time = time.time()


    if comparison.response:
        comparison.execution_in_seconds = int(end_time - start_time)
        comparison.save()

    return comparison.criteria_choice # boolen representing result -> True = criteria_1