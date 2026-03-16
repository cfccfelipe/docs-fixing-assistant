from pydantic import BaseModel


class AgentRequest(BaseModel):
    prompt: str


class AgentResponse(BaseModel):
    content: str
    status: str = "success"
