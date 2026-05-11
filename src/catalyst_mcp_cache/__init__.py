"""MCP/tool-cache wedge powered by catalyst-brain."""

from catalyst_mcp_cache.core import CatalystMCPPage, CatalystMCPRegistry
from catalyst_mcp_cache.license import COMMERCIAL_CONTACT, LicenseError, assert_research_use

__version__ = "0.2.0"

__all__ = [
    "COMMERCIAL_CONTACT",
    "CatalystMCPPage",
    "CatalystMCPRegistry",
    "LicenseError",
    "assert_research_use",
    "__version__",
]
