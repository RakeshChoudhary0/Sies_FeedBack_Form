"""
Supabase Client Wrapper
Provides access to Supabase services (Auth, Storage, Database, Realtime)
via the official supabase-py SDK when credentials are configured.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY: str = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
    or ""
).strip()

_supabase_client = None

def get_supabase_client():
    """
    Returns an initialized Supabase Client, or None if credentials are missing
    or supabase library is not installed.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client
    except ImportError:
        print("[WARNING] 'supabase' package is not installed. Run: pip install supabase")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase client: {e}")
        return None

