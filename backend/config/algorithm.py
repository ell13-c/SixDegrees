# backend/config/algorithm.py
# All algorithm tuning constants. No magic numbers in algorithm code — change here only.

ALPHA: float = 0.6   # Weight for profile distance component
BETA: float = 0.4    # Weight for interaction score component
# ALPHA + BETA must equal 1.0

INTERACTION_WEIGHTS: dict[str, float] = {
    "likes":    0.3,
    "comments": 0.5,
    "dms":      0.2,
    # To add a new interaction type:
    # 1. Add column to interactions table in Supabase
    # 2. Add entry here (weights must sum to 1.0)
    # Zero logic changes required anywhere else.
}

# Mirrors DEFAULT_WEIGHTS from services/matching/scoring.py.
# Kept here so map_pipeline/ can import without depending on matching/ directly.
PROFILE_WEIGHTS: dict[str, float] = {
    "interests":       0.35,
    "location":        0.20,
    "languages":       0.15,
    "field_of_study":  0.10,
    "industry":        0.10,
    "education_level": 0.05,
    "age":             0.05,
}
