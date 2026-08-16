"""MCP 2026-07-28 stateless adapter for Powerfarm Kernel Compute."""

from .server import MCP_PROTOCOL_VERSION, create_server

__all__ = ["MCP_PROTOCOL_VERSION", "create_server"]
