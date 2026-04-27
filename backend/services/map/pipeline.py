"""Global coordinate pipeline orchestrator.

Chains the five pipeline stages in order:

1. ``fetcher.fetch()`` -- load all profiles and interactions from Supabase.
2. ``distance.build_combined_distance()`` -- build the N x N distance matrix.
3. ``projector.project()`` -- reduce to 2D with UMAP.
4. ``validation.validate_output()`` -- sanity-check the UMAP output.
5. ``writer.write()`` -- normalise and upsert coordinates.

A ``pipeline_runs`` record is written on both success and failure for
observability.
"""
import time
from services.map.fetcher import fetch
from services.map.distance import build_combined_distance
from services.map.projector import project
from services.map.validation import validate_output
from services.map.writer import write
from services.map.diagnostics import record_run
from services.map.contracts import PipelineInput, PipelineResult


def run() -> PipelineResult:
    """Execute the full global coordinate pipeline.

    Fetches all data, builds the combined distance matrix, runs UMAP,
    validates and writes results, and records a diagnostics entry.

    Returns:
        PipelineResult: Ordered user IDs, 2D coordinates, interaction edge
        count, and total wall-clock duration.

    Raises:
        Exception: Re-raises any exception after recording a ``failed`` run
            in ``pipeline_runs``.
    """
    start = time.time()
    data: PipelineInput | None = None
    try:
        data = fetch()
        matrix = build_combined_distance(data)
        coords = project(matrix)
        validate_output(coords, data.user_ids)
        write(data.user_ids, coords)
        duration_ms = int((time.time() - start) * 1000)
        edge_count = sum(
            1 for r in data.interactions
            if (r.get("likes_count") or 0) + (r.get("comments_count") or 0) > 0
        )
        result = PipelineResult(
            user_ids=data.user_ids,
            coords=coords,
            edge_count=edge_count,
            duration_ms=duration_ms,
        )
        record_run(
            status="success",
            user_count=len(data.user_ids),
            edge_count=edge_count,
            duration_ms=duration_ms,
            error=None,
        )
        return result
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        record_run(
            status="failed",
            user_count=len(data.user_ids) if data else 0,
            edge_count=0,
            duration_ms=duration_ms,
            error=str(e),
        )
        raise


def run_pipeline_for_user(user_id: str) -> None:
    """Compatibility shim — calls the global pipeline."""
    if not user_id or not isinstance(user_id, str):
        raise ValueError("user_id must be a non-empty string")
    run()
