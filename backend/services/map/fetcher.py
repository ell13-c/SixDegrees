"""Fetches all profiles and interactions from Supabase for the pipeline.

This module is the first stage of the global coordinate pipeline. It reads
every row from ``public.profiles`` and ``public.interactions`` and bundles
them into a ``PipelineInput`` that the downstream stages consume.
"""

from config.settings import get_supabase_client
from models.user import UserProfile
from services.map.contracts import PipelineInput


def fetch() -> PipelineInput:
    """Fetch all user profiles and interaction rows from Supabase.

    Returns:
        PipelineInput: Profiles parsed into ``UserProfile`` objects and raw
        interaction dicts ready for the distance matrix stage.
    """
    sb = get_supabase_client()
    profiles_rows = sb.table("profiles").select("*").execute().data
    interactions_rows = sb.table("interactions").select("*").execute().data
    profiles = [UserProfile(**row) for row in profiles_rows]
    return PipelineInput(profiles=profiles, interactions=interactions_rows)
