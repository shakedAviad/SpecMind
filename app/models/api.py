from pydantic import BaseModel


class AskRequest(BaseModel):
    session_id: str | None = None
    question: str


class AskResponse(BaseModel):
    session_id: str
    answer: str


class HealthStatus(BaseModel):
    status: str
