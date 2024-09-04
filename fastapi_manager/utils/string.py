import re


def convert_to_snake_case(string: str):
    pattern = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
    return pattern.sub("_", string).lower()


def convert_to_camel_case(string: str, is_upper: bool = False):
    s = re.sub(r"(_|-)+", " ", string).title().replace(" ", "")
    return "".join([s[0].upper() if is_upper else s[0].lower(), s[1:]])


def is_camel_case(string: str):
    CAMEL_CASE_TEST_RE = re.compile(
        r"^[a-zA-Z]*([a-z]+[A-Z]+|[A-Z]+[a-z]+)[a-zA-Z\d]*$"
    )
    return CAMEL_CASE_TEST_RE.match(string) is not None


def is_snake_case(string: str):
    SNAKE_CASE_TEST_RE = re.compile(r"^([a-z]+\d*_[a-z\d_]*|_+[a-z\d]+[a-z\d_]*)$")
    return SNAKE_CASE_TEST_RE.match(string) is not None