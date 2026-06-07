import json
from zabbix_client import get_cpu_usage, get_power_usage
from prompt import build_intent_prompt, build_general_prompt, build_tool_classifier_message, explain_realtime_metrics, rag_prompt
from config import OLLAMA_GENERATE_URL, JOKE_URL, OLLAMA_CHAT_URL
import requests
from rag.rag_pipeline import answer_with_rag

def call_ollama_generate(chat_context_payload: dict) -> dict:
    response = requests.post(OLLAMA_GENERATE_URL,
        json=chat_context_payload
    )
    try:
        return response.json()
    except ValueError:
        print(f"call_ollama_generate: failed to parse JSON response: {response.text}")
        return {}


def call_ollama_chat(chat_context_payload: dict) -> dict:
    response = requests.post(
        OLLAMA_CHAT_URL,
        json=chat_context_payload
    )
    print(f"Ollama chat response: {response.json()}")
    return response.json()["message"]["content"]

def call_ollama_chat_old(user_message: str) -> dict:
    response = requests.post(
        OLLAMA_CHAT_URL,
        json={
            "model": "mistral",
            "messages": build_tool_classifier_message(user_message=user_message),
            "format": "json",  # important
            "stream": True  # we want to stream for better performance
        }
    )
    print(f"Ollama chat response: {response.json()}")
    return response.json()["message"]["content"]


def intent_classification(user_message: str) -> dict:

    intent_prompt = build_intent_prompt(user_input=user_message)
    # prompt = user_message

    # Example: calling local Ollama
    result = call_ollama_generate(intent_prompt)
    # Defensive: the generate endpoint should return a `response` field.
    raw = result.get("response") if isinstance(result, dict) else None
    if raw is None:
        print(f"intent_classification: unexpected generate result: {result}")
        return {"category": {"category": "unknown"}}

    try:
        intent = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        intent = raw

    print(f'Intent classification result: {intent}')
    return {"category": intent}


def parse_action(user_message: str) -> str:
        
        action_tool_response = call_ollama_chat(user_message)
        print(f"Action tool response: {action_tool_response}")
        return action_tool_response

def generate_general_info(chat_context_payload: dict) -> str:
    print("Generating general information...")
    # general_prompt = build_general_prompt(user_input=chat_context_payload["messages"][-1]["content"])
    response = call_ollama_chat(chat_context_payload)
    if not isinstance(response, dict):
        print(f"generate_general_info: non-dict response: {response}")
        return str(response)

    # Prefer `response`, but fall back to chat-style `message.content` if present
    if "response" in response:
        return response["response"]

    if "message" in response and isinstance(response["message"], dict):
        return response["message"].get("content", json.dumps(response))

    print(f"generate_general_info: unexpected response shape: {response}")
    return json.dumps(response)


def call_ollama_chat_explain(real_time_metric: str) -> str:
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

def generate_with_rag(query: str) -> str:
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


def prepare_chat_context_payload(new_user_message: str, chat_history: list):

    ollama_messages = []
    for msg in chat_history:
        ollama_messages.append({
            "role": "assistant" if msg['role'] == 'bot' else 'user',
            "content": msg['text']
        })

    # 3. Append the brand new user message to the end of the payload
    ollama_messages.append({
        "role": "user",
        "content": new_user_message
    })

    # 4. Payload for Ollama's Chat Endpoint
    payload = {
        "model": "mistral",
        "messages": ollama_messages,
        "stream": False,
        "options": {
            "temperature": 0.7  # Optional: tweaks creativity
        }
    }

    return payload



def process_llm_call(chat_context_payload: dict) -> str:
    print("Processing LLM call...")

    # # intent_result = intent_classification(user_message)

    # intent_result["category"] = 'info'
    # category = intent_result["category"]
    # category['category'] = 'info'  # For testing, force all messages into "info" category
    category = {}
    category['category'] = 'info'  # For testing, force all messages into "info" category
    print(f"Intent classification category: {category}")

    if category['category'] == "info":
        print("Handling info category")
        return generate_general_info(chat_context_payload)

    # elif category['category'] == "knowledge":
    #     print("Handling knowledge category")
    #     return generate_with_rag(user_message)

    # elif category['category'] == "action":
    #     print('Handling action category')
    #     try:
    #         res_parse_action = json.loads(parse_action(user_message))
    #     except json.JSONDecodeError as e:
    #         print(f"Failed to parse action JSON: {e}")
    #         return generate_general_info(user_message)

    #     print(f"Parsed tool: {res_parse_action}")

    #     tool = res_parse_action.get('action', '')
    #     arguments = res_parse_action.get('arguments', {})

    #     allowed_tools = ["get_cpu_usage", "get_power_usage"]
    #     if tool in allowed_tools:
    #         try:
    #             if tool == "get_cpu_usage":
    #                 cpu_info = get_cpu_usage(arguments)
    #                 explanation = call_ollama_chat_explain(cpu_info)
    #                 print(f"Explanation for CPU usage: {explanation}")
    #                 return explanation

    #             elif tool == "get_power_usage":
    #                 power_info = get_power_usage(arguments)
    #                 explanation = call_ollama_chat_explain(power_info)
    #                 print(f"Explanation for power usage: {explanation}")
    #                 return explanation
    #         except Exception as e:
    #             print(f"Error calling tool {tool}: {e}")
    #             return generate_general_info(user_message)
    #     else:
    #         print(f"Unknown tool '{tool}' received from LLM, defaulting to info response.")
    #         return generate_general_info(user_message)

    # print("Unrecognized intent category, defaulting to general info response.")
    # return generate_general_info(user_message)
 