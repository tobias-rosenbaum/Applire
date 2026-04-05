"""
Entry point: python -m apliqa.mcp

Starts the Apliqa MCP server.  Only stdio transport is supported in the
Community Edition.  SSE transport is reserved for the Cloud Edition.

Usage:
    cd backend
    python -m apliqa.mcp
"""
import os
import sys


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    if transport != "stdio":
        print(
            f"ERROR: MCP_TRANSPORT={transport!r} is not supported in the Community Edition. "
            "Only 'stdio' is available.",
            file=sys.stderr,
        )
        sys.exit(1)

    from applire.mcp.server import mcp

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
