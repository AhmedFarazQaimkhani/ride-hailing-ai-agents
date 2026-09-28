#!/usr/bin/env python3
"""Run the Driver Co-Pilot web UI (LinkedIn-ready demo)."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("ENV") != "production"
    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
    )
