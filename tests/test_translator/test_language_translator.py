from languages.translator import Translator
from languages.message_types import TextMessage, CodeLanguageMessage
import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_aenter_aexit():
    async with Translator(files_path=Path("src/languages")) as translator:
        assert translator is not None
        assert translator._language_path is not None
        assert translator._languages != {}


@pytest.mark.asyncio
async def test_translate_not_code_language():
    async def mock_messages():
        yield TextMessage(text=("hello world",))

    async with Translator(files_path=Path("src/languages")) as translator:
        async for message in translator.translate(mock_messages()):
            assert message == TextMessage(text=("hello world",))


@pytest.mark.parametrize(
    ["code_language", "parameters", "expected"],
    [
        pytest.param(
            "test_code_with_no_parameters",
            [],
            {"text": ["Test Line 1", "Test Line 2"]},
            id="text_code_no_parameters",
        ),
        pytest.param(
            "test_code_with_no_parameters",
            [
                "param_1=parameter_1",
                "param_2=parameter_2",
                "param_3=parameter_3",
            ],
            {"text": ["Test Line 1", "Test Line 2"]},
            id="text_code_no_parameters_sending_parameters",
        ),
        pytest.param(
            "test_code_with_parameters",
            [
                "param_1=parameter_1",
                "param_2=parameter_2",
                "param_3=parameter_3",
            ],
            {"text": ["Parameter 1 is", "parameter_1"]},
            id="text_code_no_parameters_sending_parameters",
        ),
        pytest.param(
            "not_existing_code",
            [],
            {"text": ["not_existing_code"]},
            id="not_existing_code",
        ),
    ],
)
@pytest.mark.asyncio
async def test_translate_code_language(code_language, parameters, expected: dict[str, list[str]]):
    async def mock_messages():
        yield CodeLanguageMessage(code_language=code_language, parameters=tuple(parameters))

    async with Translator(files_path=Path("src/languages")) as translator:
        async for message in translator.translate(mock_messages()):
            assert message == TextMessage(text=tuple(expected['text']))
