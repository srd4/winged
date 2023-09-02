import requests
import json
import time
from winged_app.models import ItemVsTwoCriteriaAIComparison, Item
import os

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

INCREMENT = 0.1  # Decrease sleep time by this much with each success
MIN_SLEEP = 0.5  # Don't go below this

PERCENTAGE_CHUNK = 20  # 10% of total items as a chunk

class ItemReclassifier:
    def __init__(self):
        self.SLEEP_TIME = 2.0

    def reclassify_items(self, items, criteria_1, criteria_2, comparison_function):
        total = len(items)
        chunk_size = max(1, (total * PERCENTAGE_CHUNK) // 100)  # At least one item per chunk
        count = 0
        updated_items = []
        
        for item in items:
            try:
                result, self.SLEEP_TIME = comparison_function(item, criteria_1, criteria_2)
            except Exception as e:
                print(f"An error occurred classifying item {item.pk}: {e}")
                continue

            item.actionable = result
            updated_items.append(item)
            count += 1
            print(f"{count}/{total} processed. '{item}' \nsent to {'actionable' if result else 'non-actionable'}.")

            # Update in chunks based on percentage
            if len(updated_items) >= chunk_size:
                Item.objects.bulk_update(updated_items, ['actionable'])
                updated_items = []

        # Update any remaining items
        if updated_items:
            Item.objects.bulk_update(updated_items, ['actionable'])


    def compute_zero_shot_comparison(self, item, criteria_1, criteria_2):

        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        data = {
            "inputs": item.statement,
            "parameters": {"candidate_labels": [criteria_1, criteria_2]}
        }

        MAX_RETRIES = 3
        for retry_count in range(MAX_RETRIES):
            try:
                time.sleep(self.SLEEP_TIME)
                response = requests.post(API_URL, headers=headers, json=data)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

                self.SLEEP_TIME = max(MIN_SLEEP, self.SLEEP_TIME - INCREMENT)

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

                return response_json, response_json['labels'][0] == criteria_1
            
            except requests.RequestException as e:
                if response.status_code == 503 or response.status_code == 429:
                    print(f"Hit rate limit. Sleeping for a bit longer.")
                    self.SLEEP_TIME *= 2
                    time.sleep(self.SLEEP_TIME)  # Exponential backoff
                    
                print(f"API call failed due to a network issue (requests.RequestException): {e}")
                print(f"Retry {retry_count + 1}: {e}")
                time.sleep(5)
            except Exception as e:
                print(f"Failed for some unknown Exception\nRetry {retry_count + 1}: {e}")
                time.sleep(5)
                


    def item_vs_criteria(self, item, criteria_1, criteria_2, force_recompute=False):
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
            return comparison.criteria_choice

        start_time = time.time()
        response, comparison.criteria_choice = self.compute_zero_shot_comparison(
            item,
            criteria_1.statement_version.statement,
            criteria_2.statement_version.statement,
            self.SLEEP_TIME
        )
        end_time = time.time()
        comparison.execution_in_seconds = int(end_time - start_time)

        if response:
            comparison.response = response
            comparison.save()

        return comparison.criteria_choice