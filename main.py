import json
from prompt import explain_realtime_metrics
from zabbix_client import get_cpu_usage, get_power_usage
from fastapi import FastAPI, Request, UploadFile, HTTPException, File
from datetime import datetime
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from llm import call_ollama_chat_explain, call_ollama_chat_explain, intent_classification, generate_general_info, parse_action, generate_with_rag
import requests  # if calling local llama / ollama
from rag.ingest import handle_file
from agent.react_agent import run_react_agent

app = FastAPI()
 

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/agent", response_class=HTMLResponse)
async def agent_ui(request: Request):
    return templates.TemplateResponse("agent.html", {"request": request})

@app.post("/agent")
async def agent(req: ChatRequest):
    user_message = req.message
    print(f"Agent : Received user message: {user_message}")
    result = run_react_agent(user_query=user_message)
    return JSONResponse(result)


    


@app.get("/add-dox", response_class=HTMLResponse)
async def add_dox_ui(request: Request):
    return templates.TemplateResponse("add_dox.html", {"request": request})

@app.post("/upload-dox", response_class=HTMLResponse)
async def add_dox(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    return JSONResponse(await handle_file(file))


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
 
        

    
    


"""
Add this route to your existing main.py.
It exposes POST /agent  →  runs the ReAct loop  →  returns the full trace.
"""
 

from agent.react_agent import run_react_agent
 
# ── Add this route ────────────────────────────────────────────────────────────
 
@app.post("/agent")
async def agent_chat(req: ChatRequest):
    result = run_react_agent(req.message)
    return JSONResponse(result)
 
# ─────────────────────────────────────────────────────────────────────────────
# The route returns this shape:
#
# {
#   "final_answer": "RACK-C2 is at 99 % power utilisation and 27.8 °C inlet ...",
#   "total_steps": 3,
#   "steps": [
#     {
#       "step": 1,
#       "type": "tool_call",
#       "thought": "I need to check which servers are in RACK-C2 first.",
#       "action": "list_servers_in_rack",
#       "action_input": {"rack_id": "RACK-C2"},
#       "observation": "{\"servers\": [\"PROD2\", \"PROD3\"]}"
#     },
#     {
#       "step": 2,
#       "type": "tool_call",
#       "thought": "Now I should check power and cooling for RACK-C2.",
#       "action": "get_rack_power",
#       "action_input": {"rack_id": "RACK-C2"},
#       "observation": "{\"watts\": 4950, \"capacity_watts\": 5000, \"utilisation_pct\": 99}"
#     },
#     {
#       "step": 3,
#       "type": "final_answer",
#       "thought": "I have enough data to give a complete answer.",
#       "content": "RACK-C2 is near capacity at 99 % (4950/5000 W) ..."
#     }
#   ]
# }
# ─────────────────────────────────────────────────────────────────────────────

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