import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.models.config import ModelProvider
from app.services.config_service import ConfigService


def test_delete_llm_config_handles_string_provider():
    service = ConfigService()
    config = SimpleNamespace(
        llm_configs=[
            SimpleNamespace(provider="aihubmix", model_name="gpt-5.4"),
            SimpleNamespace(provider="deepseek", model_name="deepseek-chat"),
        ]
    )

    service.get_system_config = AsyncMock(return_value=config)
    service.save_system_config = AsyncMock(return_value=True)

    result = asyncio.run(service.delete_llm_config("aihubmix", "gpt-5.4"))

    assert result is True
    assert [(item.provider, item.model_name) for item in config.llm_configs] == [
        ("deepseek", "deepseek-chat"),
    ]
    service.save_system_config.assert_awaited_once_with(config)


def test_delete_llm_config_handles_enum_provider():
    service = ConfigService()
    config = SimpleNamespace(
        llm_configs=[
            SimpleNamespace(provider=ModelProvider.AIHUBMIX, model_name="gpt-5.4"),
            SimpleNamespace(provider=ModelProvider.OPENAI, model_name="gpt-4o"),
        ]
    )

    service.get_system_config = AsyncMock(return_value=config)
    service.save_system_config = AsyncMock(return_value=True)

    result = asyncio.run(service.delete_llm_config("aihubmix", "gpt-5.4"))

    assert result is True
    assert [
        (service._provider_to_string(item.provider), item.model_name)
        for item in config.llm_configs
    ] == [("openai", "gpt-4o")]
    service.save_system_config.assert_awaited_once_with(config)