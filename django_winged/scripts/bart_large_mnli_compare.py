import requests
import json
import time
from winged_app.models import ItemVsTwoCriteriaAIComparison
import os

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"


def compute_zero_shot_comparison(item, criteria_1, criteria_2):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    data = {
        "inputs": item.statement,
        "parameters": {"candidate_labels": [criteria_1, criteria_2]}
    }

    MAX_RETRIES = 3
    for retry_count in range(MAX_RETRIES):
        try:
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

            # Check for a loading model and retry.
            while 'estimated_time' in response.json():
                for i in range(int(response.json()['estimated_time'])):
                    time.sleep(1)
                    print("model is loading", i / response.json()['estimated_time'])
                response = requests.post(API_URL, headers=headers, json=data)

            response_json = response.json()

            # Validate that 'labels' exists in the response
            if 'labels' not in response_json:
                raise ValueError("Invalid response: 'labels' key missing")

            return response_json, response_json['labels'][0] == criteria_1
        
        except requests.RequestException as e:
            raise ValueError(f"API call failed due to a network issue: {e}")
        except Exception as e:
            print(f"Retry {retry_count + 1}: {e}")
            time.sleep(5)
            


def item_vs_criteria(item, criteria_1, criteria_2, force_recompute=False):
    comparison, created = ItemVsTwoCriteriaAIComparison.objects.get_or_create(
        ai_model="bart-large-mnli",
        criteria_1=criteria_1.statement_version,
        criteria_2=criteria_2.statement_version,
        item_compared=item,
    )

    if not created and not force_recompute:
        return comparison.criteria_choice

    start_time = time.time()
    comparison.response, comparison.criteria_choice = compute_zero_shot_comparison(
        item,
        criteria_1.statement_version.statement,
        criteria_2.statement_version.statement
    )
    end_time = time.time()
    comparison.execution_in_seconds = int(end_time - start_time)
    comparison.save()

    time.sleep(10)

    return comparison.criteria_choice