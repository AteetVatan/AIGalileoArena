"""
Debug entry-point for the Galileo Arena backend.

Usage
-----
  python debug.py              # normal debug run (hot-reload, DEBUG log)
  python debug.py --wait       # pause until a remote debugger attaches (debugpy)
  python debug.py --port 5679  # custom debugpy listen port

Run directly or use your IDE's "Python: Current File" launch config so
breakpoints, watches, and step-through all work out of the box.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

# ---------------------------------------------------------------------------
# 1. Force DEBUG-friendly defaults before anything else imports `settings`
# ---------------------------------------------------------------------------
os.environ.setdefault("LOG_LEVEL", "DEBUG")

logger = logging.getLogger("debug")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Galileo Arena – debug server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Uvicorn listen port (default: 8000)",
    )
    parser.add_argument(
        "--debugpy-port",
        type=int,
        default=5678,
        help="debugpy listen port (default: 5678)",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for a remote debugger to attach before starting the server",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable hot-reload (useful when debugpy is attached)",
    )
    return parser.parse_args()


def _attach_debugpy(*, port: int, wait: bool) -> None:
    """Start a debugpy listener so VS Code / Cursor can attach."""
    try:
        import debugpy  # noqa: WPS433 — optional import
    except ImportError:
        logger.warning(
            "debugpy is not installed – skipping remote-debug listener. "
            "Install with:  pip install debugpy"
        )
        return

    debugpy.listen(("0.0.0.0", port))
    logger.info("debugpy listening on 0.0.0.0:%s", port)

    if wait:
        logger.info("Waiting for debugger to attach …")
        debugpy.wait_for_client()
        logger.info("Debugger attached – resuming startup.")


def main() -> None:
    args = _parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    )

    # ── Optional debugpy attachment ──────────────────────────────────────
    if args.wait or "--wait" in sys.argv:
        _attach_debugpy(port=args.debugpy_port, wait=True)
    else:
        _attach_debugpy(port=args.debugpy_port, wait=False)

    # ── Launch uvicorn programmatically ──────────────────────────────────
    import uvicorn  # noqa: WPS433 — deferred so debugpy hooks first

    use_reload = not args.no_reload

    logger.info(
        "Starting Galileo Arena  host=%s  port=%s  reload=%s",
        args.host,
        args.port,
        use_reload,
    )

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=use_reload,
        log_level="debug",
    )


if __name__ == "__main__":
    main()
