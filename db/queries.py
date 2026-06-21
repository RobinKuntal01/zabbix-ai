from supabase import Client
from fastapi import FastAPI, Depends, HTTPException, status
from db.database import get_supabase_user 


class Queries:

    async def get_user_by_id(self, user_id, db: Client = Depends(get_supabase_user)):

        profile = (
                db.table("profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )
        print(f"Profile: {profile}" )
        return profile
    
    async def get_company_by_user_id(self, user_id, db: Client = Depends(get_supabase_user)):

        company = (
                db.table("company")
                .select("id, company_name, profiles!inner(id)") # Pull the company ID
                .eq("profiles.id", user_id)
                .single()
                .execute()
            )
        print(f"Company: {company}" )
        return company

   