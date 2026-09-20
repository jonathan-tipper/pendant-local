"""Read local Pendant status; optionally capture without deleting device pages."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import httpx

from pendant_api.config import Settings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, help="Same directory passed to pendant-local serve")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--capture", action="store_true", help="Download for up to 60 seconds, with no page deletion")
    args = parser.parse_args()
    try:
        settings = Settings.load(args.data_dir)
        with httpx.Client(
            base_url=f"http://127.0.0.1:{args.port}",
            headers={"Authorization": f"Bearer {settings.token}"},
            timeout=httpx.Timeout(180, connect=5),
            trust_env=False,
        ) as client:
            info = client.get("/v1/device")
            info.raise_for_status()
            print(json.dumps(info.json(), indent=2))
            if args.capture:
                response = client.post("/v1/captures", json={
                    "acknowledge": False,
                    "idle_timeout": 5,
                    "max_seconds": 60,
                })
                response.raise_for_status()
                print(json.dumps(response.json(), indent=2))
        return 0
    except httpx.HTTPStatusError as exc:
        # Includes capture IDs and preservation status for failed capture jobs.
        print(f"API returned HTTP {exc.response.status_code}: {exc.response.text}", file=sys.stderr)
    except (httpx.RequestError, OSError, ValueError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
