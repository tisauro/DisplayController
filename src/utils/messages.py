messages_template = [
    {"background_color": [100, 0, 0]},  # change display background color
    {"text": ["hello world"]},  # raw text no translation applies
    {"code_language": "test_code_with_no_parameters"},  # simple language code
    {
        "code_language": "test_code_with_parameters"
    },  # the parameter name is used instead because the value of the parameter is not provided
    {
        "code_language": "test_code_with_no_parameters",
        "parameters": ["param_1=parameter_1"],
    },  # the parameter is ignored
    {
        "code_language": "test_code_with_parameters",
        "parameters": ["param_1=parameter_1"],
    },  # the parameter is used
    {
        "code_language": "long_text_with_parameters",
        "parameters": [
            "param_1=parameter_1",
            "param_2=parameter_2",
            "param_3=parameter_3",
        ],
    },
    {"code_language": "long_text_even_no_lines"},
    {"code_language": "long_text_odd_no_lines"},
]


async def dispatch_messages():
    for message in messages_template:
        yield message


if __name__ == "__main__":

    async def main():
        async for message in dispatch_messages():
            print(message)

    from asyncio import run

    run(main())
