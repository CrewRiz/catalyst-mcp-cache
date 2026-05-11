# Catalyst MCP Cache

Source-available MCP progressive-discovery adapter powered by the closed-source,
monetized `catalyst-brain` SDK.

This repo is a wedge: researchers and agent builders can integrate and test the
workflow, while the core engine remains in `catalyst-brain`. Production,
enterprise, hosted, revenue-generating, or customer-pilot use requires a written
license or pilot agreement.

```text
hello@strategic-innovations.ai
```

## What It Does

MCP agents often burn context on repeated tool schemas, full tool catalogs, and
large stdout/stderr payloads. `catalyst-mcp-cache` keeps those heavy objects
behind Catalyst-backed compact references:

| Capability | Adapter behavior |
|---|---|
| Progressive `tools/list` | Returns compact MCP-shaped tool records with `$ref` schemas |
| Schema on demand | Expands a schema only after discovery or explicit lookup |
| Query-gated selection | Ranks tools with `CatalystTokenKernel.discover(...)` |
| Deferred tool results | Stores full MCP call results behind compact task refs |
| Rain state handoff | Exports compact session state for agent/serverless transfer |
| Commercial boundary | Free research/evaluation adapter; production requires a Catalyst license |

This adapter uses public SDK APIs only. It does not expose Catalyst Brain source
or trade secrets.

## Install

Install the SDK from PyPI:

```bash
python -m pip install catalyst-brain
```

Local evaluation:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install catalyst-brain
python -m pip install -e ".[dev]"
pytest -q
catalyst-mcp-cache-smoke
```

## Example

```python
from catalyst_mcp_cache import CatalystMCPRegistry

registry = CatalystMCPRegistry(dim=1024)
compact = registry.register_mcp_tool(
    {
        "name": "repo.search",
        "description": "Search repository files by text query.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "annotations": {"tags": ["repo", "search"]},
    }
)

page = registry.tools_list(limit=5)
selected = registry.select_tool("repo search", include_schema=True)
task = registry.record_tool_result(
    "repo.search",
    content=[{"type": "text", "text": "large output..." * 1000}],
)

print(page.as_mcp_response())
print(registry.expand_schema(compact["schema_ref"]))
print(selected["inputSchema"])
print(registry.fetch_result(task["result_ref"])["stdout"][:120])
print(registry.compression_report())
```

## Public API

| API | Purpose |
|---|---|
| `register_mcp_tool(tool)` | Register a standard MCP tool object |
| `tools_list(limit, cursor, include_schemas=False)` | Compact MCP-shaped `tools/list` response |
| `discover_tools(query, include_schema=False)` | Ranked MCP-shaped discovery response |
| `select_tool(query)` | Top tool for a task query |
| `expand_schema(ref_or_name)` | Resolve schema refs only when needed |
| `record_tool_result(...)` | Store full MCP result behind a compact task ref |
| `fetch_result(ref_or_task_id)` | Retrieve a deferred result explicitly |
| `rain_snapshot(agent_id=...)` | Export compact Rain state |
| `context_savings_report()` | Compare naive full context to compact Catalyst context |

Protocol mapping details are in [docs/MCP_MAPPING.md](docs/MCP_MAPPING.md).

## Claim Boundary

This repo demonstrates adapter-level context reduction and routing mechanics for
MCP-style agents. It does not claim model-quality improvements by itself, and it
does not claim physical quantum behavior. Use the public benchmark suite at
`https://github.com/CrewRiz/catalyst-brain-benchmarks` for reproducible SDK
measurements.

## License Boundary

Allowed without a commercial agreement: non-commercial research, academic
experiments, personal evaluation, benchmark reproduction, and pull requests.

Requires a written license or pilot agreement: production agents, enterprise
internal deployments, hosted MCP services, paid products, customer pilots, or
any revenue-generating workflow.

Contact `hello@strategic-innovations.ai`.
