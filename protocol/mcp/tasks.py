"""Tasks extension policy for the first stateless Kernel boundary.

Kernel operations are deliberately short, deterministic request/response calls. The
2026-07-28 Tasks extension is therefore not advertised here. Long-running operational
work belongs to Platform/ADK and must carry explicit durable handles before this module
is enabled; hidden in-process task state would violate the deployment model.
"""

TASKS_EXTENSION_ID = "io.modelcontextprotocol/tasks"
TASKS_ENABLED = False
