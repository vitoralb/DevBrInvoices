import requests
from django.utils import timezone
from core.models import ApiLog


def get_safe_payload(content_bytes) -> str:
    if not content_bytes:
        return ""
    if isinstance(content_bytes, str):
        text = content_bytes
    else:
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return "<binary data>"

    if "\x00" in text:
        return "<binary data>"
    return text


def logged_request(method, url, **kwargs):
    req_payload_raw = kwargs.get("data") or kwargs.get("json") or b""
    if isinstance(req_payload_raw, dict):
        import json

        req_payload_raw = json.dumps(req_payload_raw)

    request_payload = get_safe_payload(req_payload_raw)

    if method.upper() == "GET":
        response = requests.get(url, **kwargs)
    elif method.upper() == "POST":
        response = requests.post(url, **kwargs)
    else:
        response = requests.request(method, url, **kwargs)

    response_payload = get_safe_payload(getattr(response, "content", b""))

    ApiLog.objects.create(
        endpoint=url,
        method=method.upper(),
        request_payload=request_payload[:100000],
        response_payload=response_payload[:100000],
        status_code=response.status_code,
    )

    return response


def logged_get(url, **kwargs):
    return logged_request("GET", url, **kwargs)


def logged_post(url, **kwargs):
    return logged_request("POST", url, **kwargs)
