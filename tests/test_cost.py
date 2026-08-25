import pytest

from app.cost import calculate_cost


def test_calculate_cost_known_model():
    cost = calculate_cost(tokens_in=1_000_000, tokens_out=500_000, model="claude-sonnet-5")

    assert cost == pytest.approx(2.00 + 5.00)


def test_calculate_cost_zero_tokens():
    assert calculate_cost(tokens_in=0, tokens_out=0, model="claude-sonnet-5") == 0.0


def test_calculate_cost_unknown_model_raises():
    with pytest.raises(ValueError):
        calculate_cost(tokens_in=100, tokens_out=100, model="not-a-real-model")
