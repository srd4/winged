import os
import openai
import Levenshtein
import re
import logging
from winged_app.models import ItemVsTwoCriteriaAIComparison, Item
import time


from .sentence_transform import embedding_compare


openai.api_key = os.getenv("OPENAI_API_KEY")

def gpt_compare(criteria, item_1, item_2):
    messages=[
            {"role": "system", "content": """Choose one item from a given 
            set of two items based on a statement of values. Your output should be ONLY the string of the 
            chosen item, without any additional text. The items are strings of text of any kind. Please focus 
            solely on selecting the item that best aligns with the stated values, even if the connection 
            is vague. Remember to only output the chosen item's string."""
             },
            {"role": "user", "content": """1.'what materials are out there for the concept of 'work ethic'?'
             \n2.'Letters from a stoic - Seneca.'
             \n\nValues: something on work ethic"""
             },
            {"role": "assistant", "content": "what materials are out there for the concept of 'work ethic'?"},
            {"role": "user", "content": f"1.'{item_1}'.\n2.'{item_2}'.\n\nValues: '{criteria}'"},
        ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.2,
    )

    chosen_item = response['choices'][0]['message']['content'].strip()

    # Compute the Levenshtein distance between the chosen item and the two options.
    dist1 = Levenshtein.distance(chosen_item, item_1)
    dist2 = Levenshtein.distance(chosen_item, item_2)

    

    if dist1 < dist2:
        # item_1 is closer to criteria
        return False
    elif dist1 > dist2:
        # item_2 is closer to criteria
        return True
    else:
        print("Tie, returning item 1.")
        return False # default to keeping item_1 before item_2



default_system_prompt = """Choose one of two criteria based on a specified item. Your goal is to select the
                           criterion that best aligns with the provided item. Justify your answer succinctly
                           (tryna save tokens here). Place choosen criteria between brackets NO MATTER WHAT
                           -> {Criteria x: criteria statement here}"""


def compute_comparison(criteria_1, criteria_2, model, messages):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,
    )

    answer = response['choices'][0]['message']['content'].strip()

    matches = re.findall(r'\{(.*?)\}', answer)

    print("choosen:", matches[0])

    dist1 = Levenshtein.distance(matches[0], "criteria 1"+ criteria_1)
    dist2 = Levenshtein.distance(matches[0], "criteria 2" + criteria_2)
    
    if dist1 < dist2:
        chose_criteria_1 = True
    elif dist1 > dist2:
        chose_criteria_1 = False
    else:
        chose_criteria_1 = False

    return response, chose_criteria_1


def item_vs_criteria(item, criteria_1, criteria_2, model, system_prompt=default_system_prompt, force_recompute=False):
    comparison, created = ItemVsTwoCriteriaAIComparison.objects.get_or_create(
        ai_model=model,
        system_prompt=system_prompt,
        criteria_1=criteria_1,
        criteria_2=criteria_2,
        item_compared=item,
    )

    if not created and not force_recompute:
        return comparison.criteria_choice

    messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Item: '{item.statement}'\n\n1. Criteria_1: '{criteria_1}'\n2. Criteria_2: '{criteria_2}'"}
            ]

    start_time = time.time()
    comparison.response, comparison.criteria_choice = compute_comparison(criteria_1, criteria_2, model, messages)
    end_time = time.time()

    comparison.execution_in_seconds = int(end_time - start_time)
    comparison.save()

    return comparison.criteria_choice
