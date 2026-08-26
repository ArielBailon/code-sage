from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    code: str = Field(max_length=20_000)
    question: str = Field(max_length=2_000)


class ExplainResponse(BaseModel):
    resumen: str
    complejidad: str
    posibles_bugs: list[str]
    sugerencia: str


class RequestCost(BaseModel):
    tokens_in: int
    tokens_out: int
    model: str
    cost: float
    prompt_version: str
