"""Compatibility shim — re-exports from config.settings."""
from config.settings import get_supabase_client  # noqa: F401

# Legacy module-level singleton (tests patch this directly)
supabase = None
