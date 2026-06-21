from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client, ClientOptions
from config import settings

# Global client for general operations/service role tasks
supabase_global: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# FastAPI's built-in helper to extract the "Authorization: Bearer <JWT>" header
security = HTTPBearer()
supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
def get_supabase_user(auth: HTTPAuthorizationCredentials = Depends(security)) -> Client:
    """
    Creates a request-scoped Supabase client acting on behalf of the 
    authenticated user using their JWT token. This enforces your DB RLS policies.
    """
    jwt_token = auth.credentials # Extracts the raw JWT token string
    
    try:
        # Create a transient client instance attached to this specific user's token
        options = ClientOptions(
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        
        # 2. Instantiate the scoped client
        user_client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_KEY,
            options=options
        )
        
        # 3. Explicitly authenticate the underlying database rest client (PostgREST)
        # This acts as a bulletproof backup to make sure RLS works perfectly in Python.
        user_client.postgrest.auth(jwt_token)
        
        return {
            "client": user_client,
            "token": jwt_token
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}"
        )