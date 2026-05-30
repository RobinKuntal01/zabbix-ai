import json
import time
from zabbix_client import get_cpu_usage, get_power_usage
from fastapi import FastAPI, Request, UploadFile, HTTPException, File, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from llm import call_ollama_chat_explain, intent_classification, generate_general_info, parse_action, generate_with_rag, process_llm_call
import requests  # if calling local llama / ollama
from rag.ingest import handle_file
from agent.react_agent import run_react_agent
from redis_client import connect_redis

app = FastAPI()
 

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

async def get_current_user_id() -> str:
    return "default_user_123"

class ChatRequest(BaseModel):
    message: str
    session_id: str # Optional session ID for tracking conversations

class MessageStore(BaseModel):
    role: str        # Either "user" or "bot"
    text: str        # The raw text content
    timestamp: float # Epoch time for tracking sequence precisely

# The object schema used to store metadata in our Sidebar Hash Index
class ChatMetadata(BaseModel):
    session_id: str
    title: str
    updated_at: float


@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    return templates.TemplateResponse("chat_v2.html", {"request": request})

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
async def chat(payload: ChatRequest, 
    user_id: str = Depends(get_current_user_id)):
    try:
        print(f"Received chat request with payload: {payload} from user_id: {user_id}")
        session_id = payload.session_id
        user_message = payload.message.strip()
        current_time = time.time()

        print(f"Chat endpoint called with session_id: {session_id}, user_id: {user_id}, message: '{user_message}' at {(current_time)}")

        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        history_key = f"chat:{user_id}:{session_id}"
        sidebar_key = f"chats:{user_id}"

        redis_client = connect_redis()
        is_new_chat = await redis_client.exists(history_key) == 0

        raw_history = await redis_client.lrange(history_key, 0, -1)
        chat_context = [json.loads(msg) for msg in raw_history]

        print(f"Current chat history for session_id {session_id}: {chat_context}")
        user_msg_obj = MessageStore(role="user", text=user_message, timestamp=current_time)
        await redis_client.rpush(history_key, user_msg_obj.model_dump_json())

        print(f"Received user message: {user_message}")

        ai_reply_text = process_llm_call(user_message)

        # ai_reply_text = f"Hey! This is a real response from your FastAPI backend stored directly inside Redis list: {history_key}."
        bot_msg_obj = MessageStore(role="bot", text=ai_reply_text, timestamp=time.time())
        await redis_client.rpush(history_key, bot_msg_obj.model_dump_json())

        if is_new_chat:
            # Create a neat running title snippet using the first 30 characters of their text
            snippet_title = user_message[:30] + "..." if len(user_message) > 30 else user_message
            
            metadata = ChatMetadata(
                session_id=session_id, 
                title=snippet_title, 
                updated_at=current_time
            )
            # HSET registers it into the user's main directory hash
            await redis_client.hset(sidebar_key, session_id, metadata.model_dump_json())
        else:
            # If it's an existing chat, update its timestamp so it jumps to the top when sorted
            raw_meta = await redis_client.hget(sidebar_key, session_id)
            if raw_meta:
                meta_dict = json.loads(raw_meta)
                meta_dict["updated_at"] = current_time
                await redis_client.hset(sidebar_key, session_id, json.dumps(meta_dict))
                
        return JSONResponse({"reply": ai_reply_text})
    
    except Exception as e:
        print(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# 2. Our temporary simple user dependency
async def get_current_user_id() -> str:
    return "default_user_123"

@app.get("/test-redis")
async def test_redis(user_id: str = Depends(get_current_user_id)):
    try:
        # Define a test key unique to this user
        test_key = f"chats:{user_id}"
        
        # Write a sample payload to a Redis Hash
        sample_meta = {
            "session_id": "test-uuid-0000",
            "title": "My First Redis Chat",
            "updated_at": 1717070400.0
        }
        # print(f'test-redis: {connect_redis()}')
        # Save it into Redis
        redis_client = connect_redis()
        await redis_client.hset(test_key, "test-uuid-0000", json.dumps(sample_meta))
        
        # Instantly read it back to confirm it saved perfectly
        saved_data = await redis_client.hget(test_key, "test-uuid-0000")
        
        return {
            "status": "Success! FastAPI is connected to Windows Redis.",
            "data_read_from_redis": json.loads(saved_data)
        }
    except Exception as e:
        return {
            "status": "Connection Failed",
            "error": str(e),
            "help": "Make sure your redis-server.exe command prompt window is open!"
        }

@app.get("/sidebar")
async def get_sidebar_list(user_id: str = Depends(get_current_user_id)):
    sidebar_key = f"chats:{user_id}"
    
    # 1. Fetch all fields and values from the user's sidebar Redis Hash
    # This returns a dictionary like: {"session-uuid-1": "{'title': '...', 'updated_at': ...}"}
    redis_client = connect_redis()
    all_chats = await redis_client.hgetall(sidebar_key)
    
    parsed_list = []
    
    # 2. Loop through the raw strings from Redis and parse them into Python dictionaries
    for session_id, raw_metadata in all_chats.items():
        try:
            meta_dict = json.loads(raw_metadata)
            if isinstance(meta_dict, dict):
                # Ensure the session ID is included in every sidebar item
                meta_dict["session_id"] = session_id
                parsed_list.append(meta_dict)
        except Exception:
            continue # Skip corrupted keys if any exist
            
    # 3. Sort natively so the most recently updated chats appear at the top
    parsed_list.sort(key=lambda x: x["updated_at"], reverse=True)
    
    # Returns a clean JSON array to the frontend
    return parsed_list

@app.get("/chat-history/{session_id}")
async def get_chat_history(session_id: str, user_id: str = Depends(get_current_user_id)):
    history_key = f"chat:{user_id}:{session_id}"
    
    redis_client = connect_redis()
    raw_history = await redis_client.lrange(history_key, 0, -1)
    
    chat_history = [json.loads(msg) for msg in raw_history]
    
    return chat_history