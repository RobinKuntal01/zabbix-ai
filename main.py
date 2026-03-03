import json
from prompt import explain_realtime_metrics
from zabbix_client import get_cpu_usage, get_power_usage
from fastapi import FastAPI, Request
from datetime import datetime
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from llm import call_ollama_chat_explain, call_ollama_chat_explain, intent_classification, generate_general_info, parse_action, generate_with_rag
import requests  # if calling local llama / ollama

app = FastAPI()
 

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/chat")
async def chat(req: ChatRequest):

    user_message = req.message
    print(f"Received user message: {user_message}")

    intent_result = intent_classification(user_message)
    category = intent_result["category"]
    print(f"Intent classification category: {category}")
   
    if category['category'] == "info":
        print("Handling info category")
        general_info = generate_general_info(user_message)
        return JSONResponse(general_info)
    
    elif category['category'] == "knowledge":
        print("Handling knowledge category")
        general_info = generate_with_rag(user_message)
        return JSONResponse({"reply": general_info})
    
    elif category['category'] == "action":
        print('Handling action category')
        res_parse_action = json.loads(parse_action(user_message))
        print(f"Parsed tool: {res_parse_action}")

        tool = res_parse_action.get('action', '')
        arguments = res_parse_action.get('arguments', {})

        allowed_tools = ["get_cpu_usage", "get_power_usage"]
        if tool in allowed_tools:
            if tool == "get_cpu_usage":
                cpu_info = get_cpu_usage(arguments)
                explanation = call_ollama_chat_explain(cpu_info)
                print(f"Explanation for CPU usage: {explanation}")
                print(f"Explanation for CPU usage type: {type(explanation)}")

                # Instead of returning dict
                return JSONResponse({"reply": explanation})

            if tool == "get_power_usage":
                power_info = get_power_usage(arguments)
                explanation = call_ollama_chat_explain(power_info)
                print(f"Explanation for power usage: {explanation}")
                print(f"Explanation for power usage type: {type(explanation)}")
                return JSONResponse({"reply": explanation}) 
            

            print(f"Unknown tool '{tool}' received from LLM, defaulting to info response.")
            general_info = generate_general_info(user_message)
            return JSONResponse({"reply": general_info})
 
        

    
    




# @app.post("/zabbix-webhook")
# async def zabbix_webhook(request: Request):
#     payload = await request.json()
    
#     print("\n===== ZABBIX ALERT RECEIVED =====")
#     print("Time:", datetime.now())
#     print(payload)

#     print("\n===== SENDING ALERT TO LLAMA =====")

#     prompt = f"Hey Llama you are my cloud server troubleshooter guide. I have got this alert {payload} from my zabbix server how can i resolve it"

#     response = requests.post(
#         OLLAMA_URL,
#          json={
#              "model": "mistral",
#              "prompt": prompt,
#              "stream": False
#          },
#          timeout=120)
    

#     print(f"\n=====LLAMA RESPONSE {response.json()["response"]}=========")

    
#     return { "llama_response": response.json()["response"] }   