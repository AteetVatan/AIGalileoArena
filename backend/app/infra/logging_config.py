"""Custom logging -- shorten absolute paths to relative in log output."""

from __future__ import annotations

import logging
from pathlib import Path


def _shorten_path(text: str, workspace_normalized: str) -> str:
    """Replace workspace-absolute paths with relative ones in a string."""
    if not text or not workspace_normalized:
        return text
    try:
        normalized = text.replace("\\", "/")
        if workspace_normalized not in normalized:
            return text
        relative = normalized.replace(workspace_normalized, "").lstrip("/")
        if relative.startswith(("backend/", "frontend/")):
            return relative
        if "/backend/" in normalized or normalized.endswith("/backend"):
            return f"backend/{relative}" if relative else "backend"
        if "/frontend/" in normalized or normalized.endswith("/frontend"):
            return f"frontend/{relative}" if relative else "frontend"
        return relative or "."
    except Exception:
        logger = logging.getLogger(__name__)
        logger.debug("path shortening failed for: %s", text[:80], exc_info=True)
    return text


def _detect_workspace_root() -> Path:
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "backend").exists() and (current / "frontend").exists():
            return current
        current = current.parent
    backend_dir = Path(__file__).resolve().parent.parent.parent.parent
    return backend_dir.parent if backend_dir.name == "backend" else backend_dir


class ShortPathFormatter(logging.Formatter):

    def __init__(self, *args, workspace_root: Path | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace_root = workspace_root or _detect_workspace_root()
        self._ws_norm = str(self.workspace_root).replace("\\", "/")

    def _shorten(self, text: str) -> str:
        return _shorten_path(text, self._ws_norm)

    def _shorten_logger_name(self, name: str) -> str:
        if name == "uvicorn.error":
            return "uvicorn"
        if name == "uvicorn.access":
            return "uvicorn.access"
        if name.startswith("watchfiles"):
            return "watchfiles"
        if name.startswith("app."):
            return name
        if "." in name:
            return ".".join(name.split(".")[-2:])
        return name

    def format(self, record: logging.LogRecord) -> str:
        original_name = record.name
        record.name = self._shorten_logger_name(record.name)
        try:
            message = super().format(record)
            message = self._shorten(message)
        finally:
            record.name = original_name
        return message

    def formatException(self, ei) -> str:
        import traceback
        return "".join(self._shorten(line) for line in traceback.format_exception(*ei))


class PathShorteningFilter(logging.Filter):

    def __init__(self, workspace_root: Path):
        super().__init__()
        self._ws_norm = str(workspace_root).replace("\\", "/")

    def _shorten(self, text: str) -> str:
        return _shorten_path(text, self._ws_norm)

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self._shorten(record.msg)
        if hasattr(record, "args") and record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(self._shorten(arg))
                elif isinstance(arg, (list, tuple)):
                    processed = [self._shorten(item) if isinstance(item, str) else item for item in arg]
                    new_args.append(type(arg)(processed))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        if hasattr(record, "message") and record.message:
            record.message = self._shorten(record.message)
        return True


def configure_logging(formatter: logging.Formatter | None = None) -> None:
    if formatter is None:
        formatter = ShortPathFormatter("%(asctime)s %(levelname)-8s [%(name)s] %(message)s")

    ws_root = formatter.workspace_root if isinstance(formatter, ShortPathFormatter) else _detect_workspace_root()
    path_filter = PathShorteningFilter(ws_root)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(path_filter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.addFilter(path_filter)

    # uvicorn / watchfiles have their own handlers -- override them
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access", "watchfiles", "watchfiles.main"]:
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.addHandler(handler)
        lg.addFilter(path_filter)
        lg.propagate = False
