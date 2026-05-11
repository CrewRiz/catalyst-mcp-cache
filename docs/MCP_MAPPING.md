# MCP Mapping

`catalyst-mcp-cache` keeps the MCP surface familiar while moving heavy payloads
behind Catalyst-backed references.

| MCP concept | Adapter mapping |
|---|---|
| `tools/list` | `CatalystMCPRegistry.tools_list(...)` |
| Tool `inputSchema` | `{"$ref": "hkvc://tool/<fingerprint>/schema"}` until expanded |
| Tool selection | `discover_tools(...)` or `select_tool(...)` |
| Tool call result | `record_tool_result(...)` returns compact status plus `result_ref` |
| Explicit result fetch | `fetch_result(result_ref)` |
| Agent/session handoff | `rain_snapshot(agent_id=...)` |

The adapter is intentionally conservative: clients can request full schemas
before invocation, and full tool results remain retrievable by explicit
reference. The optimization is context placement, not removal of information.

## Boundary

This repo is source-available adapter code. The performance primitive is the
closed-source `catalyst-brain` SDK installed from PyPI. Commercial, hosted,
enterprise, revenue-generating, or customer-pilot usage requires a written
license or pilot agreement via `hello@strategic-innovations.ai`.
