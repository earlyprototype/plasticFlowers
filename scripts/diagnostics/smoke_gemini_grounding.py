"""Manual smoke test for Gemini Google Search grounding via ResearcherAgent.

Exercises the REAL Gemini API — do NOT run in CI.

Usage:
    backend/.venv/Scripts/python.exe scripts/smoke_gemini_grounding.py "CeADAR"

The script resolves imports by inserting the repo root onto sys.path, so it
can be run from any working directory as long as the path above is used.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Insert repo root so `import backend.app...` resolves regardless of cwd.
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


async def main() -> None:
    label: str = sys.argv[1] if len(sys.argv) > 1 else "CeADAR"

    from backend.app.config import get_settings
    from backend.app.agents.researcher import ResearcherAgent

    settings = get_settings()
    api_key = settings.gemini_api_key.get_secret_value()
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set — set it in .env or the environment before running this script.")
        sys.exit(1)

    print(f"Researching: {label!r}")
    agent = ResearcherAgent()
    ref = await agent._research_with_gemini(
        session_id="smoke",
        node_id="node-smoke",
        label=label,
        entity_type="organisation",
        query=f"{label} official website",
    )

    print("\n--- canonical_summary (first 240 chars) ---")
    print(ref.canonical_summary[:240])

    print("\n--- sources ---")
    if ref.sources:
        for src in ref.sources:
            print(f"  {src.url}")
    else:
        print("  (no sources returned)")


if __name__ == "__main__":
    asyncio.run(main())
