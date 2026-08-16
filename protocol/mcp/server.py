"""Powerfarm Kernel MCP 2026-07-28 stateless Streamable HTTP server."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from mcp.server import CacheHint, MCPServer
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from service.runtime import KernelRuntime, build_runtime_from_env
from worker.github_webhook import MAX_BODY_BYTES, WebhookError, accept_delivery

from .auth import auth_from_env
from .resources import install_resources
from .tools import install_tools

MCP_PROTOCOL_VERSION = "2026-07-28"
SERVER_VERSION = "0.2.0"


def create_server(
    runtime: KernelRuntime | None = None,
    *,
    auth_settings: AuthSettings | None = None,
    token_verifier: TokenVerifier | None = None,
    auth_required: bool | None = None,
) -> MCPServer[object]:
    if auth_required is None:
        env_auth, env_verifier, auth_required = auth_from_env()
        auth_settings = auth_settings or env_auth
        token_verifier = token_verifier or env_verifier
    elif not auth_required:
        auth_settings = None
        token_verifier = None
    if auth_required and (auth_settings is None or token_verifier is None):
        raise RuntimeError("OAuth settings and token verifier are required")
    owned_runtime = runtime is None
    runtime = runtime or build_runtime_from_env(auth_required=bool(auth_required))

    @asynccontextmanager
    async def lifespan(_: MCPServer[object]) -> AsyncIterator[object]:
        try:
            yield runtime
        finally:
            if owned_runtime:
                runtime.close()

    server: MCPServer[object] = MCPServer(
        name="powerfarm-kernel",
        title="Powerfarm Kernel",
        description="Stateless deterministic constitutional compute over exact ledger cuts.",
        instructions=(
            "Platform proposes. Kernel computes. Ledgers remember. Use evaluate before commit; "
            "never infer authority from MCP transport state."
        ),
        version=SERVER_VERSION,
        auth=auth_settings,
        token_verifier=token_verifier,
        lifespan=lifespan,
        cache_hints={
            "tools/list": CacheHint(ttl_ms=300_000, scope="public"),
            "resources/list": CacheHint(ttl_ms=300_000, scope="public"),
            "resources/templates/list": CacheHint(ttl_ms=300_000, scope="public"),
            "resources/read": CacheHint(ttl_ms=0, scope="private"),
        },
    )
    install_tools(server, runtime)
    install_resources(server, runtime)

    @server.custom_route(  # type: ignore[untyped-decorator]
        "/health", methods=["GET"], include_in_schema=False
    )
    async def health(_: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "service": "powerfarm-kernel",
                "server_version": SERVER_VERSION,
                "mcp_protocol_version": MCP_PROTOCOL_VERSION,
                "stateless": True,
                "genesis_root_hash": os.environ.get("POWERFARM_GENESIS_ROOT", "unset"),
            }
        )

    @server.custom_route(  # type: ignore[untyped-decorator]
        "/integrations/github/webhook", methods=["POST"], include_in_schema=False
    )
    async def github_webhook(request: Request) -> JSONResponse:
        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            return JSONResponse({"error": "payload too large"}, status_code=413)
        home = Path(os.environ.get("POWERFARM_HOME", "."))
        try:
            created, _ = accept_delivery(
                dict(request.headers),
                body,
                os.environ.get("GITHUB_WEBHOOK_SECRET", ""),
                home / "inbox" / "github",
            )
        except WebhookError as error:
            return JSONResponse({"error": str(error)}, status_code=error.status)
        return JSONResponse({"accepted": created, "duplicate": not created}, status_code=202)

    return server


def main() -> None:
    host = os.environ.get("POWERFARM_BIND_HOST", "127.0.0.1")
    port = int(os.environ.get("POWERFARM_PORT", "8000"))
    create_server().run(
        "streamable-http",
        host=host,
        port=port,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
