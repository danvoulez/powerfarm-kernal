"""Compatibility entry point for the MCP 2026-07-28 stateless server."""

from protocol.mcp.server import main as run_mcp_server

if __name__ == "__main__":
    run_mcp_server()
