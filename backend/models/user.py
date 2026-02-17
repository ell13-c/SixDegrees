from pydantic import BaseModel


class UserProfile(BaseModel):
    id: str
    interests: list[str]       # predefined hobby/interest tags
    languages: list[str]       # languages spoken
    city: str
    state: str
    education_level: str       # e.g. "bachelors", "masters", "phd", "highschool"
    field_of_study: str        # e.g. "Computer Science", "Biology"
    occupation: str            # e.g. "Software Engineer"
    industry: str              # e.g. "Technology", "Healthcare"
    age: int


class MatchResult(BaseModel):
    user: UserProfile
    score: float               # similarity score in [0, 1], higher = more similar
    tier: int                  # 1 = closest, 2 = second degree, 3 = third degree
