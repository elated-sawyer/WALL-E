import os
import sys
import openai
import time
import json
from tenacity import (
    retry,
    stop_after_attempt, # type: ignore
    wait_random_exponential, # type: ignore
)

from typing import Optional, List
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


Model = Literal["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo", "text-davinci-003", "gpt-3.5-turbo-instruct"]

# openai.api_key = os.getenv('OPENAI_API_KEY')

# @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
# def get_completion(prompt: str, temperature: float = 0.0, max_tokens: int = 256, stop_strs: Optional[List[str]] = None) -> str:
#     response = openai.Completion.create(
#         model='gpt-4o-mini',
#         prompt=prompt,
#         temperature=temperature,
#         max_tokens=max_tokens,
#         top_p=1,
#         frequency_penalty=0.0,
#         presence_penalty=0.0,
#         stop=stop_strs,
#     )
#     return response.choices[0].text

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def get_completion(prompt: str, temperature: float = 0.0, max_tokens: int = 256, stop_strs: Optional[List[str]] = None) -> str:
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]
    response = openai.ChatCompletion.create(
        model='gpt-4o-mini', # gpt-4o
        messages=messages,
        max_tokens=max_tokens,
        stop=stop_strs,
        temperature=temperature,
    )

    tokens_used = {
        "prompt_tokens": response['usage']['prompt_tokens'],
        "completion_tokens": response['usage']['completion_tokens'],
        "total_tokens": response['usage']['total_tokens']
    }

    time.sleep(0.2)
    with open('/home/**/Workspace/reflexion/reflexion_run_logs/tokenuse.log', 'a') as f:
        f.write(json.dumps(tokens_used) + '\n')  

    return response.choices[0]["message"]["content"]

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def get_chat(prompt: str, model: Model, temperature: float = 0.0, max_tokens: int = 256, stop_strs: Optional[List[str]] = None, is_batched: bool = False) -> str:
    assert model != "text-davinci-003"
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        stop=stop_strs,
        temperature=temperature,
    )
    tokens_used = {
        "prompt_tokens": response['usage']['prompt_tokens'],
        "completion_tokens": response['usage']['completion_tokens'],
        "total_tokens": response['usage']['total_tokens']
    }

    time.sleep(0.2)
    with open('/home/**/Workspace/reflexion/reflexion_run_logs/tokenuse.log', 'a') as f:
        f.write(json.dumps(tokens_used) + '\n')  
    return response.choices[0]["message"]["content"]




