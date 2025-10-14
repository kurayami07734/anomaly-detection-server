import base64
import json
from typing import Any


def encode_base64(data: dict[str, Any]) -> str:
    """
    Serializes a dictionary to a JSON string, then base64 encodes it.

    :param data: The dictionary to encode.
    :return: A base64 encoded string.
    """
    json_string = json.dumps(data)
    base64_bytes = base64.b64encode(json_string.encode("utf-8"))
    return base64_bytes.decode("utf-8")


def decode_base64(base64_string: str) -> dict[str, Any]:
    """
    Decodes a base64 string into bytes, then deserializes the JSON string to a dictionary.
    """
    json_bytes = base64.b64decode(base64_string.encode("utf-8"))
    return json.loads(json_bytes.decode("utf-8"))
