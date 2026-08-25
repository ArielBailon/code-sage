from pydantic import BaseModel


class ExplainRequest(BaseModel):
    code: str
    question: str


class ExplainResponse(BaseModel):
    resumen: str
    complejidad: str
    posibles_bugs: list[str]
    sugerencia: str
