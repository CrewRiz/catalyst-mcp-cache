from __future__ import annotations

import json

import pytest


def _tool(index: int) -> dict:
    return {
        "name": f"sandbox.tool_{index}",
        "description": "Run Python safely as a deferred tool task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source code to execute in a constrained deferred task.",
                },
                "timeout_ms": {
                    "type": "integer",
                    "description": "Maximum execution time before the task is marked failed.",
                },
                "capture_stdout": {
                    "type": "boolean",
                    "description": "Whether stdout should be retained behind the task result reference.",
                },
                "working_directory": {
                    "type": "string",
                    "description": "Repository-relative working directory for the tool invocation.",
                },
            },
            "required": ["code"],
            "additionalProperties": False,
        },
        "annotations": {"tags": ["python", "execution", "sandbox"]},
    }


def test_mcp_manifest_schema_refs_and_expansion():
    from catalyst_mcp_cache import CatalystMCPRegistry

    registry = CatalystMCPRegistry(dim=1024)
    compact = registry.register_mcp_tool(_tool(0))

    page = registry.tools_list(limit=1)
    response = page.as_mcp_response()

    assert response["tools"][0]["name"] == "sandbox.tool_0"
    assert response["tools"][0]["inputSchema"] == {"$ref": compact["schema_ref"]}
    assert response["catalyst"]["savedContextTokens"] > 0
    assert page.compact_bytes < page.full_bytes

    expanded = registry.expand_schema(compact["schema_ref"])
    assert expanded["properties"]["code"]["type"] == "string"

    full_page = registry.tools_list(limit=1, include_schemas=True)
    assert full_page.tools[0]["inputSchema"]["properties"]["timeout_ms"]["type"] == "integer"


def test_discovery_deferred_results_and_context_savings():
    from catalyst_mcp_cache import CatalystMCPRegistry

    registry = CatalystMCPRegistry(dim=1024)
    for i in range(12):
        registry.register_mcp_tool(_tool(i))

    found = registry.discover_tools("run python code", include_schema=True)
    assert found[0]["inputSchema"]["properties"]["code"]["type"] == "string"

    selected = registry.select_tool("python sandbox", include_schema=False)
    assert selected["inputSchema"]["$ref"].startswith("hkvc://tool/")

    task = registry.record_tool_result(
        "sandbox.tool_0",
        content=[{"type": "text", "text": "x" * 20_000}],
        structured_content={"bytes": 20_000},
    )
    assert task["saved_context_tokens"] > 4000

    fetched = registry.fetch_result(task["result_ref"])
    payload = json.loads(fetched["stdout"])
    assert payload["structuredContent"]["bytes"] == 20_000

    report = registry.context_savings_report()
    assert report["saved_pct"] > 80.0
    assert report["deferred_results"] == 1

    compression = registry.compression_report()
    assert compression["commercial_contact"] == "hello@strategic-innovations.ai"
    assert compression["context_saved_tokens"] == report["saved_context_tokens"]


def test_rain_snapshot_and_capabilities():
    from catalyst_brain import rain_from_header
    from catalyst_mcp_cache import CatalystMCPRegistry

    registry = CatalystMCPRegistry(dim=1024)
    registry.register_mcp_tool(_tool(0))
    snapshot = registry.rain_snapshot(agent_id="mcp-session")
    restored = rain_from_header(snapshot["rain_header"])

    assert restored.agent_id == "mcp-session"
    assert snapshot["estimated_reduction_ratio"] >= 0.0
    assert registry.capabilities()["schema_on_demand"] is True


def test_license_boundary():
    from catalyst_mcp_cache import CatalystMCPRegistry, LicenseError

    with pytest.raises(LicenseError):
        CatalystMCPRegistry(purpose="production enterprise")
