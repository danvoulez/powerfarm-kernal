from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import pytest

from worker.github_webhook import WebhookError, accept_delivery


def headers(body: bytes, secret: str, delivery: str = "delivery-1") -> dict[str, str]:
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return {
        "X-GitHub-Delivery": delivery,
        "X-GitHub-Event": "release",
        "X-Hub-Signature-256": f"sha256={signature}",
    }


def test_accepts_and_deduplicates_signed_delivery(tmp_path: Path) -> None:
    body = b'{"action":"published"}'
    first, path = accept_delivery(headers(body, "secret"), body, "secret", tmp_path)
    second, duplicate_path = accept_delivery(headers(body, "secret"), body, "secret", tmp_path)

    assert first is True
    assert second is False
    assert duplicate_path == path
    envelope = json.loads(path.read_text())
    assert envelope["event"] == "release"
    assert envelope["payload_sha256"] == hashlib.sha256(body).hexdigest()


def test_rejects_invalid_signature(tmp_path: Path) -> None:
    body = b'{"action":"published"}'
    with pytest.raises(WebhookError, match="signature") as raised:
        accept_delivery(headers(body, "wrong"), body, "secret", tmp_path)
    assert raised.value.status == 401


def test_rejects_unsupported_event(tmp_path: Path) -> None:
    body = b"{}"
    request_headers = headers(body, "secret")
    request_headers["X-GitHub-Event"] = "issues"
    with pytest.raises(WebhookError, match="unsupported") as raised:
        accept_delivery(request_headers, body, "secret", tmp_path)
    assert raised.value.status == 422
