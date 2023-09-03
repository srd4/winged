import os
import openai
import Levenshtein
import time

openai.api_key = os.getenv("OPENAI_API_KEY")

def gpt_compare(criteria, item_1, item_2):
    time.sleep(1)
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