"""Records pipeline run metadata to the pipeline_runs table."""

from config.settings import get_supabase_client


def record_run(
    status: str,
    user_count: int,
    edge_count: int,
    duration_ms: int,
    error: str | None,
) -> None:
    """Insert a pipeline run record into ``public.pipeline_runs``.

    Called on every pipeline execution regardless of outcome so that
    operators can track run history, failure rates, and performance trends.

    Args:
        status: One of ``"success"``, ``"failed"``, or ``"skipped"``.
        user_count: Number of profiles processed in the run.
        edge_count: Number of user pairs with at least one interaction.
        duration_ms: Wall-clock time for the run in milliseconds.
        error: Error message string on failure, or ``None`` on success/skip.
    """
    get_supabase_client().table("pipeline_runs").insert({
        "status": status,
        "user_count": user_count,
        "edge_count": edge_count,
        "duration_ms": duration_ms,
        "error": error,
    }).execute()
