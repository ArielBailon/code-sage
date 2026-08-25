import json

from app.models import ExplainResponse

_FIELD_NAMES = {"resumen", "complejidad", "posibles_bugs", "sugerencia"}


class FieldStreamParser:
    """Parses a fixed-order, line-per-field text stream into ExplainResponse fields."""

    def __init__(self) -> None:
        self._buffer = ""
        self._fields: dict[str, object] = {}

    def feed(self, chunk: str) -> list[tuple[str, object]]:
        self._buffer += chunk
        completed: list[tuple[str, object]] = []
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            name, _, raw_value = line.partition(":")
            name = name.strip()
            if name not in _FIELD_NAMES:
                continue
            value = json.loads(raw_value.strip())
            self._fields[name] = value
            completed.append((name, value))
        return completed

    def finalize(self) -> ExplainResponse:
        return ExplainResponse(**self._fields)
