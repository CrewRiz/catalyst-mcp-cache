from __future__ import annotations

COMMERCIAL_CONTACT = "hello@strategic-innovations.ai"
COMMERCIAL_TERMS = {"commercial", "enterprise", "hosted", "pilot", "production", "revenue", "saas"}


class LicenseError(RuntimeError):
    pass


def assert_research_use(purpose: str = "research") -> None:
    lowered = purpose.lower()
    if any(term in lowered for term in COMMERCIAL_TERMS):
        raise LicenseError(
            "Catalyst MCP Cache is research/evaluation source-available. "
            f"Commercial or production use requires a license: {COMMERCIAL_CONTACT}."
        )
