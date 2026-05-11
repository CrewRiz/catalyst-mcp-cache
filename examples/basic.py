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
