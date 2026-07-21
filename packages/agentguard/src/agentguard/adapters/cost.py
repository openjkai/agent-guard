"""Model pricing table for cost estimation."""

from __future__ import annotations

from dataclasses import dataclass

from agentguard.tracing.models import Cost, Usage


@dataclass(frozen=True)
class ModelPricing:
    input_per_million: float
    output_per_million: float


DEFAULT_PRICING: dict[str, ModelPricing] = {
    "gpt-4o": ModelPricing(2.50, 10.00),
    "gpt-4o-mini": ModelPricing(0.15, 0.60),
    "gpt-4.1": ModelPricing(2.00, 8.00),
    "gpt-4.1-mini": ModelPricing(0.40, 1.60),
    "claude-3-5-sonnet-20241022": ModelPricing(3.00, 15.00),
    "claude-3-5-haiku-20241022": ModelPricing(0.80, 4.00),
    "openrouter/auto": ModelPricing(1.00, 3.00),
    "mock-model": ModelPricing(0.0, 0.0),
}


def estimate_cost(
    model: str, usage: Usage, pricing: dict[str, ModelPricing] | None = None
) -> Cost:
    table = pricing or DEFAULT_PRICING
    rates = table.get(model)
    if rates is None:
        for key, value in table.items():
            if model.startswith(key.split("-")[0]):
                rates = value
                break
    if rates is None:
        rates = ModelPricing(1.0, 3.0)

    input_usd = (usage.input_tokens / 1_000_000) * rates.input_per_million
    output_usd = (usage.output_tokens / 1_000_000) * rates.output_per_million
    return Cost(input_usd=round(input_usd, 8), output_usd=round(output_usd, 8))
