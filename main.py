import json
import profile
import time
import uuid
from zabbix_client import get_cpu_usage, get_power_usage
from fastapi import FastAPI, Request, UploadFile, HTTPException, File, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from supabase import create_client, Client
from pydantic import BaseModel
from llm import call_ollama_chat_explain, intent_classification, generate_general_info, parse_action, generate_with_rag, prepare_chat_context_payload, process_llm_call
import requests  # if calling local llama / ollama
from rag.ingest import handle_file
from agent.react_agent import run_react_agent
from redis_client import connect_redis
from db.database import get_supabase_user, supabase_admin
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.queries import Queries

app = FastAPI()

spa_exists = os.path.exists("frontend/dist")

app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

security = HTTPBearer()

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
        return FileResponse("frontend/dist/index.html")

@app.get("/agent", response_class=HTMLResponse)
async def agent_ui(request: Request):
        return FileResponse("frontend/dist/index.html")
    

@app.post("/agent")
async def agent(req: ChatRequest):
    user_message = req.message
    print(f"Agent : Received user message: {user_message}")
    result = run_react_agent(user_query=user_message)
    return JSONResponse(result)


@app.get("/add-dox", response_class=HTMLResponse)
async def add_dox_ui(request: Request):
    return FileResponse("frontend/dist/index.html")

@app.get("/login", response_class=HTMLResponse)
async def login_ui(request: Request):
    return FileResponse("frontend/dist/index.html")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all_spa(request: Request, full_path: str):
    return FileResponse("frontend/dist/index.html")

@app.post("/upload-dox", response_class=HTMLResponse)
async def add_dox(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and text files are accepted.")
    
    return JSONResponse(await handle_file(file))


@app.post("/chat")
async def chat(payload: ChatRequest, 
    supabase_auth: dict = Depends(get_supabase_user)):
    try:
        db = supabase_auth["client"]
        token = supabase_auth["token"]
        token_details = db.auth.get_claims(jwt=token)

        claims = token_details["claims"]
        print(f"Token claims: {claims}")
        current_user_id = claims.get("sub")  # 'sub' is the standard JWT key for User UUID
        company_id = claims.get("company_id")

        if not current_user_id or not company_id or company_id == "null":
            raise HTTPException(status_code=401, detail="Unauthorized: Tenant identity missing from session token.")

        # print(f"Received chat request with payload: {payload} from user_id: {user}")
        user_message = payload.message.strip()
        current_time = time.time()
        session_id = payload.session_id

        print(f'company_id: {company_id}, current_user_id: {current_user_id}, user_message: {user_message}')

        history_key = f"tenant:{company_id}:user:{current_user_id}:chats:{session_id}"
        sidebar_key = f"tenant:{company_id}:user:{current_user_id}"

        print(f"Target Redis List Key for chat history: {history_key}")
        print(f"Target Redis Hash Key for sidebar: {sidebar_key}")

        redis_client = connect_redis()
        is_new_chat = await redis_client.exists(history_key) == 0

        raw_history = await redis_client.lrange(history_key, 0, -1)
        chat_context = [json.loads(msg) for msg in raw_history]

        print(f"Current chat history for session_id {session_id}: {chat_context}")
        print(f"Current chat history  {chat_context}")
        user_msg_obj = MessageStore(role="user", text=user_message, timestamp=current_time)
        await redis_client.rpush(history_key, user_msg_obj.model_dump_json())

        print(f"Received user message: {user_message}")
        return 
        chat_context_payload = prepare_chat_context_payload(user_message, chat_context)

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


@app.get("/test-redis")
async def test_redis():
    try:
       
        # 1. Fetch data from Supabase
        # print(f"User response from Supabase: {auth_response}")
        # response = (
        #     db.table("company")
        #     .select("id, company_name, profiles!inner(id)") # Pull the company ID
        #     .eq("profiles.id", current_user_id)
        #     .execute()
        # )
        # object_queries = Queries()
        # res_company = await object_queries.get_company_by_user_id(1, db=db)
        res_company = supabase_admin.table("company").select("*").eq("id", 1).execute()

        print(f"Supabase response {res_company}")
        return
        # Ensure we actually got data back to prevent IndexError
        if res_company.data:
            company_id = res_company.data[0]['id']      # Safely use the integer/UUID ID, not the name
            user_uuid = current_user_id
            session_uuid = str(uuid.uuid4())         # Generate a fresh UUID for this unique chat session
            
            # 2. Structure the proper Redis Key
            # Format: tenant:{company_id}:user:{user_uuid}:chats
            redis_key = f"tenant:{company_id}:user:{user_uuid}:chats"
            print(f"Target Redis Hash Key: {redis_key}")
            
            # 3. Create clean metadata payload
            sample_meta = {
                "session_id": session_uuid,          # This is clean: just the UUID string
                "title": "My First Redis Chat",
                "updated_at": time.time()            # Generates current timestamp dynamically
            }
            
            # 4. Save to Redis
            redis_client = connect_redis()
            
            # HSET stores it perfectly: 
            # Key -> tenant:1:user:UUID:chats
            # Field -> session_uuid (The specific chat ID)
            # Value -> JSON metadata string
            await redis_client.hset(redis_key, session_uuid, json.dumps(sample_meta))
            
            print(f"Successfully saved session {session_uuid} under user hash.")
        else:
            print("No company/profile found for this user.")


    except Exception as e:
        return {
            "status": "Connection Failed",
            "error": str(e),
            "help": "Make sure your redis-server.exe command prompt window is open!"
        }

@app.get("/sidebar")
async def get_sidebar_list(supabase_auth: dict = Depends(get_supabase_user)):
    db = supabase_auth["client"]
    token = supabase_auth["token"]

    auth_response = db.auth.get_user(jwt=token)
    if not auth_response or not auth_response.user:
        raise HTTPException(status_code=401, detail="User session invalid")

    obj_queries = Queries()
    current_user_id = auth_response.user.id
    print(f"Current user ID: {current_user_id}")
    res_profile = await obj_queries.get_user_by_id(current_user_id, db=db)

    print(f"Profile: {res_profile}" )
    
    get_tenant_id = await obj_queries.get_company_by_user_id(current_user_id, db=db)
    if not get_tenant_id:
        raise HTTPException(status_code=404, detail="Tenant not found for user")


    print(f"Tenant ID for user {current_user_id}: {get_tenant_id}")
    
    tenant_id = get_tenant_id.data['id']  # Assuming the response structure contains 'data' with 'id'
    company_id = tenant_id
    sidebar_key = f"tenant:{company_id}:user:{current_user_id}"
    
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
async def get_chat_history(session_id: str, supabase_auth: dict = Depends(get_supabase_user)):
    user_client = supabase_auth["client"]
    token = supabase_auth["token"]

    auth_response = user_client.auth.get_user(jwt=token)
    if not auth_response or not auth_response.user:
        raise HTTPException(status_code=401, detail="User session invalid")

    user_id = auth_response.user.id
    history_key = f"chat:{user_id}:{session_id}"
    
    redis_client = connect_redis()
    raw_history = await redis_client.lrange(history_key, 0, -1)
    
    chat_history = [json.loads(msg) for msg in raw_history]
    
    return chat_history