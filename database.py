from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

class SupabaseClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance.client = None
        return cls._instance
    
    def __init__(self):
        if self.client is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
            
            self.client: Client = create_client(supabase_url, supabase_key)
    
    def get_client(self) -> Client:
        return self.client
