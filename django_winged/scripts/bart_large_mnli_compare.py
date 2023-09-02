import requests
import json
import time
from winged_app.models import ItemVsTwoCriteriaAIComparison
import os

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

INCREMENT = 0.1  # Decrease sleep time by this much with each success
MIN_SLEEP = 0.5  # Don't go below this

def compute_zero_shot_comparison(item, criteria_1, criteria_2, sleep_time):

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    data = {
        "inputs": item.statement,
        "parameters": {"candidate_labels": [criteria_1, criteria_2]}
    }

    MAX_RETRIES = 3
    for retry_count in range(MAX_RETRIES):
        try:
            time.sleep(sleep_time)
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

            sleep_time = max(MIN_SLEEP, sleep_time - INCREMENT)

            response_json = response.json()

            # Check for a loading model and retry and wait the time.
            while 'estimated_time' in response_json:
                for i in range(int(response_json['estimated_time'])):#wait seconds it says it takes to load.                    
                    print("model is loading", i / response.json()['estimated_time'])
                    time.sleep(1)
                response = requests.post(API_URL, headers=headers, json=data)

            # Validate that 'labels' exists in the response
            if 'labels' not in response_json:
                raise ValueError("Invalid response: 'labels' key missing")

            return response_json, response_json['labels'][0] == criteria_1, sleep_time
        
        except requests.RequestException as e:
            if response.status_code == 503:
                print(f"Hit rate limit. Sleeping for a bit longer.")
                time.sleep(sleep_time * 2)  # Exponential backoff
            print(f"API call failed due to a network issue (requests.RequestException): {e}")
            print(f"Retry {retry_count + 1}: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Failed for some unknown Exception\nRetry {retry_count + 1}: {e}")
            time.sleep(5)
            


def item_vs_criteria(item, criteria_1, criteria_2, sleep_time, force_recompute=False):
    created = False
    try:
        comparison = ItemVsTwoCriteriaAIComparison.objects.get(
            ai_model="bart-large-mnli",
            criteria_1=criteria_1.statement_version,
            criteria_2=criteria_2.statement_version,
            item_compared=item)
        
    except ItemVsTwoCriteriaAIComparison.DoesNotExist:
        created = True
        comparison = ItemVsTwoCriteriaAIComparison(
            ai_model="bart-large-mnli",
            criteria_1=criteria_1.statement_version,
            criteria_2=criteria_2.statement_version,
            item_compared=item
            )

    if not created and not force_recompute:
        return comparison.criteria_choice, sleep_time

    start_time = time.time()
    response, comparison.criteria_choice, sleep_time = compute_zero_shot_comparison(
        item,
        criteria_1.statement_version.statement,
        criteria_2.statement_version.statement,
        sleep_time
    )
    end_time = time.time()
    comparison.execution_in_seconds = int(end_time - start_time)

    if response:
        comparison.response = response
        comparison.save()

    return comparison.criteria_choice, sleep_time