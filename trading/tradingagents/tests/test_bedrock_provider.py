"""Amazon Bedrock — first-class native client via the optional langchain-aws extra.

Auth uses the AWS credential chain (no single key env); the model is a Bedrock
model ID / inference profile ID; langchain-aws is imported lazily with a clear
install hint when the [bedrock] extra is absent.
"""
import sys

import pytest

from tradingagents.llm_clients.api_key_env import get_api_key_env
from tradingagents.llm_clients.factory import create_llm_client
from tradingagents.llm_clients.validators import validate_model


@pytest.mark.unit
def test_factory_routes_bedrock():
    client = create_llm_client("bedrock", "us.anthropic.claude-opus-4-8-v1:0")
    assert type(client).__name__ == "BedrockClient"


@pytest.mark.unit
def test_bedrock_any_model_and_no_key_env():
    assert validate_model("bedrock", "any.model-id:0") is True
    # Bedrock uses the AWS credential chain, so there is no single key env.
    assert get_api_key_env("bedrock") is None


@pytest.mark.unit
def test_helpful_error_when_langchain_aws_absent(monkeypatch):
    import tradingagents.llm_clients.bedrock_client as bc
    monkeypatch.setattr(bc, "_BEDROCK_CLASS", None)
    monkeypatch.setitem(sys.modules, "langchain_aws", None)  # force ImportError on import
    with pytest.raises(ImportError, match=r"bedrock"):
        create_llm_client("bedrock", "m").get_llm()


@pytest.mark.unit
def test_construction_when_extra_installed(monkeypatch):
    pytest.importorskip("langchain_aws")
    import tradingagents.llm_clients.bedrock_client as bc
    monkeypatch.setattr(bc, "_BEDROCK_CLASS", None)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")
    llm = create_llm_client("bedrock", "us.anthropic.claude-sonnet-4-6-v1:0").get_llm()
    assert type(llm).__name__ == "NormalizedChatBedrockConverse"
    assert llm.region_name == "eu-west-1"
