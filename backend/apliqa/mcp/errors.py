"""
MCP error helpers — translate domain exceptions to structured McpError responses.
"""
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

# JSON-RPC error codes
_NOT_FOUND = -32001
_INVALID_INPUT = -32602
_INTERNAL = -32603


def not_found(msg: str) -> McpError:
    return McpError(ErrorData(code=_NOT_FOUND, message=msg))


def invalid_input(msg: str) -> McpError:
    return McpError(ErrorData(code=_INVALID_INPUT, message=msg))


def internal(msg: str) -> McpError:
    return McpError(ErrorData(code=_INTERNAL, message=msg))
