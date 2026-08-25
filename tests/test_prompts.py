import pytest

from app.prompts import get_prompt
from app.prompts.v1 import PROMPT_V1
from app.prompts.v2 import PROMPT_V2
from app.prompts.v3 import PROMPT_V3

FIELD_MARKERS = ["resumen:", "complejidad:", "posibles_bugs:", "sugerencia:"]


@pytest.mark.parametrize("prompt", [PROMPT_V1, PROMPT_V2, PROMPT_V3])
def test_prompt_field_markers_appear_in_order(prompt: str):
    positions = [prompt.index(marker) for marker in FIELD_MARKERS]

    assert positions == sorted(positions)


@pytest.mark.parametrize(
    "version, expected",
    [("v1", PROMPT_V1), ("v2", PROMPT_V2), ("v3", PROMPT_V3)],
)
def test_get_prompt_returns_matching_template(version: str, expected: str):
    assert get_prompt(version) == expected


def test_get_prompt_unknown_version_raises():
    with pytest.raises(ValueError):
        get_prompt("v4")
