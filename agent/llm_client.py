import openai
from .config import OPENAI_API_KEY, MODEL_NAME, MAX_TOKENS, TEMPERATURE

openai.api_key = OPENAI_API_KEY

def chat(messages, **kwargs):
    """
    messages: list of {"role": "system/user/assistant", "content": "..."}
    returns the assistant’s content string.
    """
    resp = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        **kwargs
    )
    return resp.choices[0].message.content
