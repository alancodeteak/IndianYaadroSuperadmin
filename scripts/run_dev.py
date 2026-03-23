import os
import sys
from pathlib import Path

import uvicorn


def main() -> None:
    # Ensure `app` package imports work even when running this file directly.
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() in {"1", "true", "yes"}

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        app_dir=str(project_root),
        reload_dirs=[str(project_root / "app")],
    )


if __name__ == "__main__":
    main()

