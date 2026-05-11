from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from catalyst_brain import CatalystTokenKernel, ToolPage, ToolSpec

from catalyst_mcp_cache.license import COMMERCIAL_CONTACT, assert_research_use


def _canonical_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _json_bytes(value: Any) -> int:
    return len(_canonical_json(value).encode("utf-8"))


def _estimate_tokens(byte_count: int) -> int:
    return max(1, (byte_count + 3) // 4)


def _saved_pct(compact_bytes: int, full_bytes: int) -> float:
    if full_bytes <= 0:
        return 0.0
    return round(max(0.0, 100.0 * (1.0 - compact_bytes / full_bytes)), 4)


def _normalise_tags(tags: Iterable[str]) -> Tuple[str, ...]:
    out: List[str] = []
    for tag in tags:
        clean = str(tag).strip()
        if clean and clean not in out:
            out.append(clean)
    return tuple(out)


def _tags_from_mcp_tool(tool: Dict[str, Any]) -> Tuple[str, ...]:
    annotations = tool.get("annotations") or {}
    tags = tool.get("tags") or annotations.get("tags") or annotations.get("catalyst:tags") or ()
    if isinstance(tags, str):
        tags = (tags,)
    return _normalise_tags(tags)


@dataclass(frozen=True)
class CatalystMCPPage:
    """MCP-shaped compact tools/list response plus Catalyst savings metrics."""

    tools: List[Dict[str, Any]]
    next_cursor: Optional[str]
    compact_bytes: int
    full_bytes: int

    @property
    def saved_context_tokens(self) -> int:
        return max(0, _estimate_tokens(self.full_bytes) - _estimate_tokens(self.compact_bytes))

    @property
    def saved_pct(self) -> float:
        return _saved_pct(self.compact_bytes, self.full_bytes)

    def as_mcp_response(self) -> Dict[str, Any]:
        return {
            "tools": self.tools,
            "nextCursor": self.next_cursor,
            "catalyst": {
                "compactBytes": self.compact_bytes,
                "fullBytes": self.full_bytes,
                "savedContextTokens": self.saved_context_tokens,
                "savedPct": self.saved_pct,
            },
        }


class CatalystMCPRegistry:
    """Progressive MCP tool registry backed by the catalyst-brain SDK.

    The adapter keeps full MCP tool descriptors and full tool results outside
    the agent context until the agent asks for the schema or result by reference.
    """

    def __init__(self, *, dim: int = 4096, purpose: str = "research") -> None:
        assert_research_use(purpose)
        self.purpose = purpose
        self.kernel = CatalystTokenKernel(dim=dim)
        self._tool_names: List[str] = []
        self._mcp_tools: Dict[str, Dict[str, Any]] = {}
        self._schema_refs: Dict[str, str] = {}
        self._task_ids: List[str] = []

    def register_tool(
        self,
        *,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        tags: Tuple[str, ...] = (),
        annotations: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register a tool from explicit fields and return a compact descriptor."""
        return self.register_mcp_tool(
            {
                "name": name,
                "description": description,
                "inputSchema": input_schema,
                "annotations": {
                    **(annotations or {}),
                    "catalyst:tags": list(tags),
                },
            }
        )

    def register_mcp_tool(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Register an MCP tool object.

        Supports the standard `inputSchema` key and accepts `input_schema` for
        Python callers. Full schemas are retained behind Catalyst references.
        """
        name = str(tool.get("name") or "").strip()
        description = str(tool.get("description") or "").strip()
        input_schema = tool.get("inputSchema", tool.get("input_schema"))
        if not name:
            raise ValueError("MCP tool requires a non-empty name")
        if not description:
            raise ValueError("MCP tool requires a non-empty description")
        if not isinstance(input_schema, dict):
            raise ValueError("MCP tool requires an inputSchema object")

        tags = _tags_from_mcp_tool(tool)
        full_tool = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "annotations": dict(tool.get("annotations") or {}),
        }
        if tags:
            full_tool["annotations"]["catalyst:tags"] = list(tags)

        if name not in self._tool_names:
            self._tool_names.append(name)
        self._mcp_tools[name] = full_tool

        compact = self.kernel.register_tool(
            ToolSpec(
                name=name,
                description=description,
                input_schema=input_schema,
                tags=tags,
            )
        )
        self._schema_refs[compact["schema_ref"]] = name
        return compact

    def compact_manifest(self, *, limit: int = 20, cursor: Optional[str] = None) -> ToolPage:
        """Return the raw Catalyst compact page."""
        return self.kernel.list_tools(limit=limit, cursor=cursor)

    def tools_list(
        self,
        *,
        limit: int = 20,
        cursor: Optional[str] = None,
        include_schemas: bool = False,
    ) -> CatalystMCPPage:
        """Return an MCP tools/list-style compact response.

        By default `inputSchema` is a compact `$ref`. Set `include_schemas=True`
        only when a client explicitly needs a full schema page.
        """
        page = self.kernel.list_tools(limit=limit, cursor=cursor)
        tools: List[Dict[str, Any]] = []
        for item in page.tools:
            name = item["name"]
            annotations = {
                "catalyst:fingerprint": item["fingerprint"],
                "catalyst:schemaRef": item["schema_ref"],
                "catalyst:tags": list(item.get("tags", [])),
            }
            tool = {
                "name": name,
                "description": item["description"],
                "inputSchema": self.expand_schema(name) if include_schemas else {"$ref": item["schema_ref"]},
                "annotations": annotations,
            }
            tools.append(tool)

        compact_bytes = _json_bytes(tools)
        full_bytes = sum(_json_bytes(self._mcp_tools[name]) for name in self._tool_names)
        return CatalystMCPPage(
            tools=tools,
            next_cursor=page.next_cursor,
            compact_bytes=compact_bytes,
            full_bytes=full_bytes,
        )

    def discover(
        self,
        query: str,
        *,
        limit: int = 5,
        include_schema: bool = False,
    ) -> List[Dict[str, Any]]:
        """Return compact ranked tools; expands schemas only on request."""
        return self.kernel.discover(query, limit=limit, include_schema=include_schema)

    def discover_tools(
        self,
        query: str,
        *,
        limit: int = 5,
        include_schema: bool = False,
    ) -> List[Dict[str, Any]]:
        """Return ranked tools in MCP shape."""
        ranked = self.discover(query, limit=limit, include_schema=include_schema)
        out: List[Dict[str, Any]] = []
        for item in ranked:
            schema_ref = item["schema_ref"]
            out.append(
                {
                    "name": item["name"],
                    "description": item["description"],
                    "inputSchema": item.get("schema") if include_schema else {"$ref": schema_ref},
                    "annotations": {
                        "catalyst:fingerprint": item["fingerprint"],
                        "catalyst:schemaRef": schema_ref,
                        "catalyst:score": item.get("score", 0.0),
                        "catalyst:why": item.get("why", []),
                    },
                }
            )
        return out

    def select_tool(self, query: str, *, include_schema: bool = True) -> Dict[str, Any]:
        """Return the top ranked MCP tool for a task query."""
        matches = self.discover_tools(query, limit=1, include_schema=include_schema)
        if not matches:
            raise LookupError("No tools registered")
        return matches[0]

    def expand_schema(self, ref_or_name: str) -> Dict[str, Any]:
        """Resolve a Catalyst schema reference or tool name to a full schema."""
        name = self._schema_refs.get(ref_or_name, ref_or_name)
        try:
            return dict(self._mcp_tools[name]["inputSchema"])
        except KeyError as exc:
            raise KeyError(f"Unknown MCP tool or schema reference: {ref_or_name}") from exc

    def defer_tool_output(
        self,
        tool_name: str,
        *,
        stdout: str = "",
        stderr: str = "",
        status: str = "completed",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store full stdout/stderr behind a compact task result reference."""
        meta = {"tool_name": tool_name, **(metadata or {})}
        compact = self.kernel.create_code_execution_task(
            code=f"mcp-tool:{tool_name}",
            stdout=stdout,
            stderr=stderr,
            status=status,
            metadata=meta,
        )
        self._task_ids.append(compact["task_id"])
        return compact

    def record_tool_result(
        self,
        tool_name: str,
        *,
        content: Optional[List[Dict[str, Any]]] = None,
        structured_content: Optional[Dict[str, Any]] = None,
        is_error: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store an MCP call result while returning only compact status."""
        payload = {
            "content": content or [],
            "structuredContent": structured_content or {},
            "isError": is_error,
        }
        return self.defer_tool_output(
            tool_name,
            stdout=_canonical_json(payload),
            stderr="",
            status="failed" if is_error else "completed",
            metadata={"mcp_result": True, **(metadata or {})},
        )

    def fetch_tool_output(self, task_id: str) -> Dict[str, Any]:
        return self.kernel.fetch_task_result(task_id)

    def fetch_result(self, ref_or_task_id: str) -> Dict[str, Any]:
        task_id = ref_or_task_id
        prefix = "hkvc://task/"
        suffix = "/result"
        if task_id.startswith(prefix) and task_id.endswith(suffix):
            task_id = task_id[len(prefix) : -len(suffix)]
        return self.fetch_tool_output(task_id)

    def rain_snapshot(self, *, agent_id: str = "catalyst-mcp-cache") -> Dict[str, Any]:
        return self.kernel.export_rain_snapshot(agent_id=agent_id)

    def context_savings_report(self) -> Dict[str, Any]:
        """Compare naive full MCP context with Catalyst compact context."""
        full_payload = {
            "tools": [self._mcp_tools[name] for name in self._tool_names],
            "toolResults": [self.kernel.fetch_task_result(task_id) for task_id in self._task_ids],
        }
        compact_payload = {
            "tools": self.tools_list(limit=max(1, len(self._tool_names))).as_mcp_response(),
            "toolResults": [self.kernel.compact_task_status(task_id) for task_id in self._task_ids],
        }
        full_bytes = _json_bytes(full_payload)
        compact_bytes = _json_bytes(compact_payload)
        return {
            "full_context_bytes": full_bytes,
            "compact_context_bytes": compact_bytes,
            "saved_pct": _saved_pct(compact_bytes, full_bytes),
            "saved_context_tokens": max(0, _estimate_tokens(full_bytes) - _estimate_tokens(compact_bytes)),
            "deferred_results": len(self._task_ids),
            "tools": len(self._tool_names),
        }

    def compression_report(self) -> Dict[str, Any]:
        page = self.compact_manifest(limit=max(1, len(self._tool_names)))
        snapshot = self.rain_snapshot()
        context = self.context_savings_report()
        return {
            "tools": len(self._tool_names),
            "manifest_compact_bytes": page.compact_bytes,
            "manifest_full_bytes": page.full_bytes,
            "manifest_saved_tokens": page.saved_context_tokens,
            "context_saved_pct": context["saved_pct"],
            "context_saved_tokens": context["saved_context_tokens"],
            "rain_estimated_reduction_ratio": snapshot["estimated_reduction_ratio"],
            "commercial_contact": COMMERCIAL_CONTACT,
        }

    def capabilities(self) -> Dict[str, Any]:
        return {
            "progressive_tool_discovery": True,
            "schema_on_demand": True,
            "deferred_tool_results": True,
            "rain_state_handoff": True,
            "sdk_dependency": "catalyst-brain",
            "commercial_contact": COMMERCIAL_CONTACT,
        }
