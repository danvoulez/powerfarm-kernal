"""Map stable service failures to bounded JSON-RPC errors."""

from __future__ import annotations

from collections.abc import Callable

from mcp.shared.exceptions import MCPError
from mcp_types import INVALID_PARAMS

from service.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    ValidationError,
)


def call_service[ResultT](operation: Callable[[], ResultT]) -> ResultT:
    try:
        return operation()
    except ValidationError as error:
        raise MCPError(INVALID_PARAMS, str(error), {"powerfarmCode": error.code}) from error
    except AuthorizationError as error:
        raise MCPError(-32001, str(error), {"powerfarmCode": error.code}) from error
    except NotFoundError as error:
        raise MCPError(-32004, str(error), {"powerfarmCode": error.code}) from error
    except ConflictError as error:
        raise MCPError(-32009, str(error), {"powerfarmCode": error.code}) from error
    except ServiceError as error:
        raise MCPError(-32050, str(error), {"powerfarmCode": error.code}) from error
