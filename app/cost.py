# Prices are USD per 1M tokens, as published by Anthropic as of 2026-06-24.
# Update this table if pricing changes or MODEL_NAME is pointed at a new model.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-5": (2.00, 10.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-fable-5": (10.00, 50.00),
}


def calculate_cost(tokens_in: int, tokens_out: int, model: str) -> float:
    if model not in MODEL_PRICING:
        raise ValueError(f"unknown model for cost calculation: {model!r}")
    input_price, output_price = MODEL_PRICING[model]
    return (tokens_in / 1_000_000) * input_price + (tokens_out / 1_000_000) * output_price
