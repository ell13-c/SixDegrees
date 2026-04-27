# Per-field similarity functions.
# All return a float in [0, 1]. Pure functions — no I/O.

# Strips common English suffixes to unify variants like cooking/cook, hiking/hike.
_STEM_SUFFIXES = ("ing", "ers", "er", "ed", "ion", "s")


def _stem(word: str) -> str:
    w = word.lower().strip()
    for suffix in _STEM_SUFFIXES:
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            return w[: -len(suffix)]
    return w


FIELD_OF_STUDY_CATEGORIES: dict[str, str] = {
    # STEM
    "computer science": "stem",
    "software engineering": "stem",
    "electrical engineering": "stem",
    "mechanical engineering": "stem",
    "civil engineering": "stem",
    "biomedical engineering": "stem",
    "mathematics": "stem",
    "statistics": "stem",
    "physics": "stem",
    "chemistry": "stem",
    "biology": "stem",
    "data science": "stem",
    # Business
    "business administration": "business",
    "finance": "business",
    "accounting": "business",
    "economics": "business",
    "marketing": "business",
    "management": "business",
    "entrepreneurship": "business",
    # Humanities
    "history": "humanities",
    "philosophy": "humanities",
    "literature": "humanities",
    "linguistics": "humanities",
    "political science": "humanities",
    "sociology": "humanities",
    "psychology": "humanities",
    # Arts
    "fine arts": "arts",
    "graphic design": "arts",
    "music": "arts",
    "film": "arts",
    "architecture": "arts",
    # Health
    "nursing": "health",
    "medicine": "health",
    "public health": "health",
    "pharmacy": "health",
    "physical therapy": "health",
}

INDUSTRY_CATEGORIES: dict[str, str] = {
    "software": "tech",
    "technology": "tech",
    "hardware": "tech",
    "cybersecurity": "tech",
    "artificial intelligence": "tech",
    "finance": "finance",
    "banking": "finance",
    "investment": "finance",
    "insurance": "finance",
    "accounting": "finance",
    "healthcare": "health",
    "pharmaceuticals": "health",
    "biotechnology": "health",
    "medical devices": "health",
    "education": "education",
    "research": "education",
    "government": "public",
    "nonprofit": "public",
    "law": "public",
    "media": "creative",
    "entertainment": "creative",
    "advertising": "creative",
    "design": "creative",
    "retail": "commerce",
    "e-commerce": "commerce",
    "manufacturing": "industry",
    "construction": "industry",
    "energy": "industry",
    "transportation": "industry",
}


def jaccard(a: list[str], b: list[str], stem: bool = False) -> float:
    """Jaccard similarity between two lists treated as sets.

    stem=True applies suffix stripping (used for interests).
    Returns 0.0 if both sets are empty.
    """
    if stem:
        set_a = {_stem(x) for x in a}
        set_b = {_stem(x) for x in b}
    else:
        set_a, set_b = set(a), set(b)
    if not set_a and not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def tiered_location(city1: str, state1: str, city2: str, state2: str) -> float:
    """Same city → 1.0 / same state → 0.5 / different → 0.0."""
    if city1 is None or state1 is None or city2 is None or state2 is None:
        return 0.0
    if city1.lower() == city2.lower():
        return 1.0
    if state1.lower() == state2.lower():
        return 0.5
    return 0.0


def tiered_categorical(a: str, b: str, category_map: dict[str, str]) -> float:
    """Exact match → 1.0 / same category → 0.5 / different → 0.0."""
    if a is None or b is None:
        return 0.0
    a_norm, b_norm = a.lower().strip(), b.lower().strip()
    if a_norm == b_norm:
        return 1.0
    cat_a = category_map.get(a_norm)
    cat_b = category_map.get(b_norm)
    if cat_a and cat_b and cat_a == cat_b:
        return 0.5
    return 0.0


def inverse_distance_age(a: int, b: int) -> float:
    """Returns 1 / (1 + |a - b|). Same age → 1.0, 10 years apart → ~0.09."""
    if a is None or b is None:
        return 0.0
    return 1.0 / (1.0 + abs(a - b))
