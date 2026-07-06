"""Model name validators for each provider."""

from .model_catalog import get_known_models


VALID_MODELS = {
    provider: models
    for provider, models in get_known_models().items()
    if provider not in ("ollama", "openrouter", "aihubmix", "custom_openai")
}


def validate_model(provider: str, model: str) -> bool:
    provider_lower = provider.lower()

    if provider_lower in ("ollama", "openrouter", "aihubmix", "custom_openai"):
        return True

    if provider_lower not in VALID_MODELS:
        return True

    return model in VALID_MODELS[provider_lower]
