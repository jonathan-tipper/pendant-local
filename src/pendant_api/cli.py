from __future__ import annotations

import argparse
import asyncio
import json
import platform
import sys
from pathlib import Path

from .config import Settings


def main():
    parser = argparse.ArgumentParser(prog="pendant-local", description="Local Limitless Pendant API. Start with scan; nothing records automatically.")
    parser.add_argument("--data-dir", type=Path)
    subs = parser.add_subparsers(dest="command", required=True)
    scan = subs.add_parser("scan", help="Discover nearby Pendants without connecting")
    scan.add_argument("--timeout", type=float, default=8)
    subs.add_parser("info", help="Connect to the configured Pendant and read status")
    configure = subs.add_parser("configure", help="Save the Bluetooth address returned by scan")
    configure.add_argument("address")
    subs.add_parser("token", help="Print the local bearer token for your own API client")
    subs.add_parser("doctor", help="Check local prerequisites without connecting to a device")
    serve = subs.add_parser("serve", help="Run the HTTP API on localhost")
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        settings = Settings.load(args.data_dir)
        if args.command == "configure":
            settings.configure_address(args.address)
            print("Pendant address saved. Next: pendant-local info")
        elif args.command == "token":
            print(settings.token)
        elif args.command == "doctor":
            print(json.dumps({"python": platform.python_version(), "system": platform.system(),
                              "data_directory": str(settings.data_dir), "device_configured": bool(settings.address),
                              "bluetooth_requirement": "Local Bluetooth adapter and OS permission. Hardware detection happens during scan.",
                              "linux_system_dbus_socket": Path("/run/dbus/system_bus_socket").exists() if sys.platform.startswith("linux") else None}, indent=2))
        elif args.command in {"scan", "info"}:
            from . import device
            from filelock import FileLock
            with FileLock(str(settings.data_dir / "service.lock"), timeout=0):
                if args.command == "scan":
                    if not 1 <= args.timeout <= 30:
                        parser.error("timeout must be between 1 and 30 seconds")
                    result = asyncio.run(device.scan(args.timeout))
                else:
                    if not settings.address:
                        parser.error("Run pendant-local scan, then pendant-local configure ADDRESS first.")
                    result = asyncio.run(device.info(settings.address))
            print(json.dumps(result, indent=2))
        else:
            import uvicorn
            from .app import create_app
            print(f"Dashboard: http://127.0.0.1:{args.port}\nAPI docs: http://127.0.0.1:{args.port}/docs\nUse `pendant-local token` to get your local login token.\nData: {settings.data_dir}\nNo device recording or download starts until requested.")
            uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port, workers=1, access_log=False)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(1, f"{type(exc).__name__}: {exc}\nRun pendant-local doctor to check the host.\n")


if __name__ == "__main__":
    main()
