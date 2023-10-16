import tiktoken

def count_tokens(text, model="gpt-4"):
    tokenizer = tiktoken.encoding_for_model(model)
    tokens = list(tokenizer.encode(text))
    return len(tokens)