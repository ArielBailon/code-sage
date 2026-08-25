from app.prompts.v1 import PROMPT_V1
from app.prompts.v2 import PROMPT_V2
from app.prompts.v3 import PROMPT_V3

PROMPT_VERSIONS: dict[str, str] = {
    "v1": PROMPT_V1,
    "v2": PROMPT_V2,
    "v3": PROMPT_V3,
}


def get_prompt(version: str) -> str:
    if version not in PROMPT_VERSIONS:
        raise ValueError(f"unknown prompt version: {version!r}")
    return PROMPT_VERSIONS[version]
