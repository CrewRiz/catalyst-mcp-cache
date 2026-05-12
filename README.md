# Catalyst MCP Cache

Source-available MCP progressive-discovery adapter powered by the public
`catalyst-brain` SDK wheel.

Researchers and agent builders can integrate and test the workflow while the
core engine remains in `catalyst-brain`. The Catalyst Brain free tier is
generous, does not require registration or signup, and does not need an API key
for early local evaluation. Most users should not hit free-tier limits during
initial integration.

When this adapter moves toward production agents, hosted MCP services,
enterprise deployment, customer pilots, or higher-volume API usage, contact:

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
| Production path | Free early evaluation; contact Catalyst for production, hosted, enterprise, or higher-quota use |

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

## Free Tier And Production Use

Install `catalyst-brain` from PyPI and evaluate this adapter without signup,
registration, or an API key. The free tier covers early research, academic
experiments, personal evaluation, benchmark reproduction, prototypes, pull
requests, and issue reports.

Most users should not hit free-tier limits during early development. If your use
case becomes production agents, hosted MCP services, enterprise deployment,
customer pilots, revenue workflows, or needs higher quotas/support, contact:

Contact `hello@strategic-innovations.ai`.
