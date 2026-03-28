from pydantic import BaseModel, ConfigDict

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    nickname: str
    bio: str | None = None
    avatar_url: str | None = None
    age: int | None = None
    city: str | None = None
    state: str | None = None
    education: str | None = None
    occupation: str | None = None
    industry: str | None = None
    interests: list[str] = []
    languages: list[str] = []
    profile_tier: int = 6
    is_admin: bool = False
