import json

import pytest
from pydantic import ValidationError

from app.response_parser import FieldStreamParser

_FULL_STREAM = (
    'resumen: "La funcion suma una lista."\n'
    'complejidad: "O(n)"\n'
    'posibles_bugs: ["No valida lista vacia"]\n'
    'sugerencia: "Usar sum()."\n'
)


def test_feed_returns_all_fields_in_order_from_one_call():
    parser = FieldStreamParser()

    completed = parser.feed(_FULL_STREAM)

    assert completed == [
        ("resumen", "La funcion suma una lista."),
        ("complejidad", "O(n)"),
        ("posibles_bugs", ["No valida lista vacia"]),
        ("sugerencia", "Usar sum()."),
    ]


def test_feed_returns_nothing_until_line_completes_across_chunks():
    parser = FieldStreamParser()

    first = parser.feed('resumen: "La funcion s')
    second = parser.feed('uma una lista."\n')

    assert first == []
    assert second == [("resumen", "La funcion suma una lista.")]


def test_finalize_returns_valid_explain_response():
    parser = FieldStreamParser()
    parser.feed(_FULL_STREAM)

    response = parser.finalize()

    assert response.resumen == "La funcion suma una lista."
    assert response.complejidad == "O(n)"
    assert response.posibles_bugs == ["No valida lista vacia"]
    assert response.sugerencia == "Usar sum()."


def test_finalize_raises_when_field_missing():
    parser = FieldStreamParser()
    parser.feed('resumen: "La funcion suma una lista."\n')

    with pytest.raises(ValidationError):
        parser.finalize()


def test_feed_raises_on_malformed_json_value():
    parser = FieldStreamParser()

    with pytest.raises(json.JSONDecodeError):
        parser.feed("resumen: not valid json\n")
