from app.services.config_service import ConfigService


def test_filter_aihubmix_models_keeps_recommended_tool_models():
    service = ConfigService()
    models = [
        {
            "model_id": "gpt-5-mini",
            "types": "llm",
            "features": "thinking,tools,function_calling",
            "input_modalities": "text,image",
            "context_length": 400000,
            "pricing": {"input": 0.25, "output": 2.0},
        },
        {
            "model_id": "random-preview-model",
            "types": "llm",
            "features": "tools",
            "input_modalities": "text",
            "context_length": 32000,
            "pricing": {"input": 0.1, "output": 0.2},
        },
        {
            "model_id": "embedding-v1",
            "types": "embedding",
            "features": "",
            "input_modalities": "text",
            "context_length": 8000,
            "pricing": {"input": 0.01, "output": 0.01},
        },
    ]

    filtered = service._filter_aihubmix_models(
        models,
        {
            "type": "llm",
            "modalities": "text",
            "features": ["tools", "function_calling"],
            "recommended_only": True,
            "tools_only": True,
            "exclude_preview": True,
            "limit": 40,
        },
    )

    assert [item["model_id"] for item in filtered] == ["gpt-5-mini"]


def test_format_aihubmix_models_maps_fields():
    service = ConfigService()
    formatted = service._format_aihubmix_models(
        [
            {
                "model_id": "gpt-5-mini",
                "desc": "fast and cheap",
                "features": "thinking,tools,function_calling",
                "context_length": "400000",
                "max_output": "128000",
                "pricing": {"input": 0.25, "output": 2.0},
            }
        ]
    )

    assert formatted == [
        {
            "id": "gpt-5-mini",
            "name": "gpt-5-mini",
            "provider_vendor": "openai",
            "description": "fast and cheap",
            "context_length": 400000,
            "max_tokens": 128000,
            "input_price_per_1k": 0.25,
            "output_price_per_1k": 2.0,
            "currency": "USD",
            "capabilities": ["thinking", "tools", "function_calling"],
        }
    ]


def test_filter_aihubmix_models_by_provider_names():
    service = ConfigService()
    models = [
        {
            "model_id": "gpt-5-mini",
            "types": "llm",
            "features": "tools,function_calling",
            "input_modalities": "text",
            "context_length": 400000,
        },
        {
            "model_id": "deepseek-v3.2",
            "types": "llm",
            "features": "tools,function_calling",
            "input_modalities": "text",
            "context_length": 128000,
        },
    ]

    filtered = service._filter_aihubmix_models(
        models,
        {
            "type": "llm",
            "modalities": "text",
            "provider_names": ["deepseek"],
            "limit": 40,
        },
    )

    assert [item["model_id"] for item in filtered] == ["deepseek-v3.2"]
