from pydantic import BaseModel


class LLMRequest(BaseModel):
    text: str


class LLMResponse(BaseModel):
    prediction: str
