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
import tempfile
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Force DEBUG-friendly defaults before anything else imports `settings`
# ---------------------------------------------------------------------------
os.environ.setdefault("LOG_LEVEL", "DEBUG")

# Configure logging as early as possible, before any other imports
from app.infra.logging_config import ShortPathFormatter, configure_logging

formatter = ShortPathFormatter(
    "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
)
configure_logging(formatter)

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
    start_time = time.time()
    logger.debug("_attach_debugpy called at %.3f (port=%s, wait=%s)", start_time, port, wait)
    
    try:
        import debugpy  # type: ignore # noqa: WPS433 — optional import
    except ImportError:
        logger.warning(
            "debugpy is not installed – skipping remote-debug listener. "
            "Install with:  pip install debugpy"
        )
        return

    # Always call listen() - it's safe to call multiple times
    # This ensures the listener is active even if called during uvicorn reload
    listen_start = time.time()
    try:
        debugpy.listen(("0.0.0.0", port))
        listen_end = time.time()
        listen_duration = (listen_end - listen_start) * 1000  # Convert to ms
        
        # Small delay to ensure port is bound before continuing
        # This helps with timing race conditions in compound launch configs
        time.sleep(0.1)
        bind_complete_time = time.time()
        
        # Create readiness file for compound launch synchronization
        # This allows preLaunchTask to wait for debugpy to be ready before attach config starts
        try:
            ready_file = Path(tempfile.gettempdir()) / f"debugpy_ready_{port}.txt"
            ready_file.write_text(f"{os.getpid()}\n{port}\n{time.time()}\n", encoding="utf-8")
            logger.debug("Readiness file created: %s", ready_file)
        except Exception as file_exc:
            logger.warning("Failed to create readiness file: %s", file_exc)
        
        logger.info(
            "debugpy listening on 0.0.0.0:%s (wait=%s, pid=%s) - ready for attach "
            "[listen_duration=%.1fms, total_setup=%.1fms]",
            port, wait, os.getpid(), listen_duration, (bind_complete_time - start_time) * 1000,
        )
    except Exception as exc:
        # If already listening, that's fine - just log and continue
        if "already listening" in str(exc).lower() or "address already in use" in str(exc).lower():
            logger.debug(
                "debugpy already listening on port %s (pid=%s)",
                port, os.getpid(),
            )
        else:
            logger.warning(
                "Failed to start debugpy listener (pid=%s): %s",
                os.getpid(), exc,
            )
            return

    if wait:
        logger.info("Waiting for debugger to attach …")
        wait_start = time.time()
        debugpy.wait_for_client()
        wait_end = time.time()
        logger.info(
            "Debugger attached – resuming startup [wait_duration=%.1fms]",
            (wait_end - wait_start) * 1000,
        )
    else:
        logger.info(
            "Server will start immediately. "
            "Use 'Python: FastAPI (Attach to debugpy)' to connect."
        )


def main() -> None:
    args = _parse_args()
    
    # Logging is already configured at module level
    # Just ensure log level is DEBUG
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Re-configure loggers in case uvicorn hasn't started yet
    # This ensures all loggers use our formatter
    from app.infra.logging_config import ShortPathFormatter, configure_logging
    formatter = ShortPathFormatter(
        "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
    )
    configure_logging(formatter)

    # ── Optional debugpy attachment ──────────────────────────────────────
    if args.wait or "--wait" in sys.argv:
        _attach_debugpy(port=args.debugpy_port, wait=True)
    else:
        _attach_debugpy(port=args.debugpy_port, wait=False)

    # ── Launch uvicorn programmatically ──────────────────────────────────
    import uvicorn  # type: ignore[import-untyped] # noqa: WPS433 — deferred so debugpy hooks first

    use_reload = not args.no_reload

    logger.info(
        "Starting Galileo Arena  host=%s  port=%s  reload=%s",
        args.host,
        args.port,
        use_reload,
    )

    # Disable uvicorn's default log config so it uses our configured loggers
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=use_reload,
        log_level="debug",
        log_config=None,  # Disable uvicorn's default log config to use ours
    )


if __name__ == "__main__":
    main()
