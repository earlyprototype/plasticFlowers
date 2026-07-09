import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


def main():
    backend_root = Path(__file__).resolve().parents[1]
    project_root = backend_root.parent
    sys.path.insert(0, str(backend_root))

    load_dotenv(project_root / ".env")

    if not os.environ.get("NEO4J_PASSWORD"):
        sys.exit(
            "ERROR: NEO4J_PASSWORD is not set.\n"
            f"Set it in {project_root / '.env'} (copy .env.example) or export it "
            "before starting the dev server."
        )

    os.environ.setdefault("PLASTICFLOWER_FAKE_LLM", "0")
    os.environ.setdefault("PLASTICFLOWER_FAKE_EMBEDDINGS", "0")

    uvicorn.run("app.main:app", host="127.0.0.1", port=8010, reload=False)


if __name__ == "__main__":
    main()
