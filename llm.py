import json

from fastapi.responses import JSONResponse
from prompt import build_intent_prompt, build_general_prompt, build_tool_classifier_message, explain_realtime_metrics, rag_prompt
from fastapi import FastAPI, Request            
from config import OLLAMA_GENERATE_URL, JOKE_URL, OLLAMA_CHAT_URL
import requests
from rag.rag_pipeline import answer_with_rag

def call_ollama_generate(prompt: str) -> dict:
    response = requests.post(OLLAMA_GENERATE_URL,
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()

def call_ollama_chat(user_message: str) -> dict:
    response = requests.post(
        OLLAMA_CHAT_URL,
        json={
            "model": "mistral",
            "messages": build_tool_classifier_message(user_message=user_message),
            "format": "json",  # important
            "stream": False
        }
    )
    print(f"Ollama chat response: {response.json()}")
    return response.json()["message"]["content"]


def intent_classification(user_message: str) -> dict:

    intent_prompt = build_intent_prompt(user_input=user_message)
    # prompt = user_message

    # Example: calling local Ollama
    result = call_ollama_generate(intent_prompt)
    intent = json.loads(result["response"])   
    print(f'Intent classification result: {intent}')
    return {"category": intent}


def parse_action(user_message: str) -> str:
        
        action_tool_response = call_ollama_chat(user_message)
        print(f"Action tool response: {action_tool_response}")
        return action_tool_response

def generate_general_info(user_message: str) -> dict:
    print("Generating general information...")
    general_prompt = build_general_prompt(user_input=user_message)
    response = call_ollama_generate(general_prompt)
    return {"reply": response["response"]}


def call_ollama_chat_explain(real_time_metric: str) -> dict:
    response = requests.post(
        OLLAMA_CHAT_URL,
        json={
            "model": "mistral",
            "messages": explain_realtime_metrics(real_time_metric),
            "stream": False
        }
    )
    print(f"Ollama chat response: {response.json()}")

    result = response.json()
    model_output = result["message"]["content"]

    return model_output

def generate_with_rag(query: str) -> dict:
    print("Generating response with RAG...")
    context = answer_with_rag(query)

    res_rag_prompt = rag_prompt(query, context)
    response = requests.post(
        OLLAMA_CHAT_URL,
        json={
            "model": "mistral",
            "messages": [{"role": "user", "content": res_rag_prompt}],
            "stream": False
        }
    )

    print(f"Ollama rag chat response: {response.json()}") 
    response = response.json()
    return response["message"]["content"]