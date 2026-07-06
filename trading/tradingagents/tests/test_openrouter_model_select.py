"""OpenRouter model selection: prompts are labeled by mode (#1000); required
prompts exit cleanly on cancel; the output-language prompt defaults to English
on cancel; and the OpenRouter list is newest-first."""

from unittest import mock

import pytest

from cli import utils


def _asks(value):
    return mock.Mock(ask=mock.Mock(return_value=value))


@pytest.mark.unit
class TestOpenRouterPromptLabel:
    @pytest.mark.parametrize("mode,label", [("quick", "Quick-Thinking"), ("deep", "Deep-Thinking")])
    def test_prompt_states_the_mode(self, mode, label):
        captured = {}

        def fake_select(message, **kwargs):
            captured["message"] = message
            return _asks("openrouter/some-model")

        with mock.patch.object(utils, "_fetch_openrouter_models",
                               return_value=[("Some Model", "openrouter/some-model")]), \
             mock.patch.object(utils.questionary, "select", side_effect=fake_select):
            out = utils.select_openrouter_model(mode)

        assert label in captured["message"]
        assert out == "openrouter/some-model"


@pytest.mark.unit
class TestOpenRouterLatestFirst:
    def test_models_sorted_newest_first(self):
        payload = {"data": [
            {"id": "old/model", "name": "Old", "created": 1000},
            {"id": "new/model", "name": "New", "created": 3000},
            {"id": "mid/model", "name": "Mid", "created": 2000},
        ]}
        resp = mock.Mock()
        resp.json.return_value = payload
        resp.raise_for_status = mock.Mock()
        with mock.patch("requests.get", return_value=resp):
            out = utils._fetch_openrouter_models()
        assert [mid for _, mid in out] == ["new/model", "mid/model", "old/model"]


@pytest.mark.unit
class TestMainstreamFilter:
    def test_dropdown_prefers_mainstream_over_niche(self):
        # _fetch returns newest-first; the shortlist should drop niche namespaces.
        models = [
            ("Fusion", "openrouter/fusion"),
            ("Niche", "nex-agi/nex-n2-pro:free"),
            ("Claude", "anthropic/claude-x"),
            ("GPT", "openai/gpt-x"),
        ]
        captured = {}

        def fake_select(message, **kwargs):
            captured["values"] = [c.value for c in kwargs["choices"]]
            return _asks("anthropic/claude-x")

        with mock.patch.object(utils, "_fetch_openrouter_models", return_value=models), \
             mock.patch.object(utils.questionary, "select", side_effect=fake_select):
            utils.select_openrouter_model("quick")

        assert "anthropic/claude-x" in captured["values"]
        assert "openai/gpt-x" in captured["values"]
        assert "openrouter/fusion" not in captured["values"]
        assert "nex-agi/nex-n2-pro:free" not in captured["values"]
        assert "custom" in captured["values"]  # escape hatch preserved

    def test_falls_back_to_all_when_no_mainstream(self):
        models = [("Niche", "nex-agi/x"), ("Other", "thedrummer/y")]
        captured = {}

        def fake_select(message, **kwargs):
            captured["values"] = [c.value for c in kwargs["choices"]]
            return _asks("nex-agi/x")

        with mock.patch.object(utils, "_fetch_openrouter_models", return_value=models), \
             mock.patch.object(utils.questionary, "select", side_effect=fake_select):
            utils.select_openrouter_model("deep")

        assert "nex-agi/x" in captured["values"]  # fallback keeps the list usable


@pytest.mark.unit
class TestCancelExitsCleanly:
    def test_dropdown_cancel_exits(self):
        with mock.patch.object(utils, "_fetch_openrouter_models", return_value=[]), \
             mock.patch.object(utils.questionary, "select", return_value=_asks(None)), \
             pytest.raises(SystemExit):
            utils.select_openrouter_model("quick")

    def test_custom_id_cancel_exits(self):
        with mock.patch.object(utils, "_fetch_openrouter_models", return_value=[]), \
             mock.patch.object(utils.questionary, "select", return_value=_asks("custom")), \
             mock.patch.object(utils.questionary, "text", return_value=_asks(None)), \
             pytest.raises(SystemExit):
            utils.select_openrouter_model("deep")

    def test_prompt_custom_model_id_cancel_exits(self):
        with mock.patch.object(utils.questionary, "text", return_value=_asks(None)), \
             pytest.raises(SystemExit):
            utils._prompt_custom_model_id()


@pytest.mark.unit
class TestLanguageDefaultsToEnglish:
    def test_select_cancel_defaults_english(self):
        with mock.patch.object(utils.questionary, "select", return_value=_asks(None)):
            assert utils.ask_output_language() == "English"

    def test_custom_language_cancel_defaults_english(self):
        with mock.patch.object(utils.questionary, "select", return_value=_asks("custom")), \
             mock.patch.object(utils.questionary, "text", return_value=_asks(None)):
            assert utils.ask_output_language() == "English"
