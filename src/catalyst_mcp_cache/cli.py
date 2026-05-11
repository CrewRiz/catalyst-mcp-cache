from __future__ import annotations

import json

from catalyst_mcp_cache import CatalystMCPRegistry


def _schema(index: int) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            f"field_{j}": {
                "type": "string" if j % 2 else "integer",
                "description": (
                    f"Verbose MCP schema field {j} for tool {index}. "
                    "This is intentionally larger than what should be repeated "
                    "inside every agent turn."
                ),
            }
            for j in range(16)
        },
        "required": ["field_0"],
    }


def main() -> int:
    registry = CatalystMCPRegistry(dim=1024)
    for i in range(24):
        registry.register_mcp_tool(
            {
                "name": f"repo.tool_{i}",
                "description": (
                    "Repository analysis MCP tool with a deliberately verbose "
                    "schema for progressive discovery evaluation."
                ),
                "inputSchema": _schema(i),
                "annotations": {"tags": ["repo", "analysis", "mcp"]},
            }
        )

    task = registry.record_tool_result(
        "repo.tool_1",
        content=[{"type": "text", "text": "line\n" * 1000}],
        structured_content={"matches": 1000},
    )
    payload = {
        "capabilities": registry.capabilities(),
        "tools_list": registry.tools_list(limit=5).as_mcp_response(),
        "selected": registry.select_tool("repo analysis", include_schema=False),
        "task": task,
        "report": registry.compression_report(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
