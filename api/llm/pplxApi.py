import os
import requests
from dotenv import load_dotenv

load_dotenv()

DECLARATIVE_SYSTEM_MSG = "You are a professional programmer completing a code review. Summarize the file at the end of your review."
API_BASE = 'https://api.perplexity.ai/chat/completions'


def get_llm_responses(repo_dict):
    llm_responses_dict = {}
    for path, item in repo_dict.items():
        if item['type'] == 'file':
            llm_response = interact_with_llm(
                item['content'], DECLARATIVE_SYSTEM_MSG)
            llm_responses_dict[path] = llm_response

    return llm_responses_dict


def interact_with_llm(message, systemMessage='Be precise and concise'):
    api_key = os.getenv('PPLX_API_KEY')

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "mistral-7b-instruct",
        "messages": [
            {
                "role": "system",
                "content": systemMessage
            },
            {
                "role": "user",
                "content": message
            }
        ]
    }

    response = requests.post(API_BASE, json=payload, headers=headers)

    return response.json()
