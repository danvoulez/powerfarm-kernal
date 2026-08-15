"""Authenticated, replay-safe ingress for GitHub App webhook deliveries."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

MAX_BODY_BYTES = 1024 * 1024
ALLOWED_EVENTS = frozenset({"ping", "push", "release", "workflow_run"})
DELIVERY_RE = re.compile(r"^[A-Za-z0-9-]{1,100}$")


class WebhookError(ValueError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def _header(headers: Mapping[str, str], name: str) -> str:
    wanted = name.casefold()
    return next((value for key, value in headers.items() if key.casefold() == wanted), "")


def accept_delivery(
    headers: Mapping[str, str], body: bytes, secret: str, inbox: Path
) -> tuple[bool, Path]:
    if not secret:
        raise WebhookError(503, "GitHub webhook secret is not configured")
    if len(body) > MAX_BODY_BYTES:
        raise WebhookError(413, "GitHub webhook payload is too large")

    signature = _header(headers, "X-Hub-Signature-256")
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected):
        raise WebhookError(401, "invalid GitHub webhook signature")

    delivery = _header(headers, "X-GitHub-Delivery")
    event = _header(headers, "X-GitHub-Event")
    if not DELIVERY_RE.fullmatch(delivery):
        raise WebhookError(400, "invalid GitHub delivery id")
    if event not in ALLOWED_EVENTS:
        raise WebhookError(422, "unsupported GitHub event")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as error:
        raise WebhookError(400, "GitHub webhook payload is not valid JSON") from error
    if not isinstance(payload, dict):
        raise WebhookError(400, "GitHub webhook payload must be a JSON object")

    inbox.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = inbox / f"{delivery}.json"
    envelope = {
        "delivery_id": delivery,
        "event": event,
        "payload": payload,
        "payload_sha256": hashlib.sha256(body).hexdigest(),
        "received_at": datetime.now(UTC).isoformat(),
    }
    data = (json.dumps(envelope, separators=(",", ":"), sort_keys=True) + "\n").encode()
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False, path
    with os.fdopen(descriptor, "wb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    return True, path
