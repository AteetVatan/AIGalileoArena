"""Custom logging formatter to shorten absolute paths in logs."""

from __future__ import annotations

import logging
from pathlib import Path


class ShortPathFormatter(logging.Formatter):
    """Formatter that replaces long absolute paths with shorter relative paths."""

    def __init__(self, *args, workspace_root: Path | None = None, **kwargs):
        """Initialize formatter with optional workspace root for path shortening."""
        super().__init__(*args, **kwargs)
        self.workspace_root = workspace_root or self._detect_workspace_root()

    @staticmethod
    def _detect_workspace_root() -> Path:
        """Detect workspace root by finding the directory containing 'backend' and 'frontend'."""
        current = Path(__file__).resolve()
        # Navigate up from backend/app/infra/logging_config.py to workspace root
        # Expected: workspace/backend/app/infra/logging_config.py
        while current.parent != current:
            if (current / "backend").exists() and (current / "frontend").exists():
                return current
            current = current.parent
        # Fallback: use backend directory if workspace root not found
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        return backend_dir.parent if backend_dir.name == "backend" else backend_dir

    def _shorten_path(self, path_str: str) -> str:
        """Replace absolute paths with relative paths in log messages."""
        if not path_str:
            return path_str

        try:
            workspace_str = str(self.workspace_root)
            workspace_normalized = workspace_str.replace("\\", "/")
            path_normalized = path_str.replace("\\", "/")
            
            # Check if workspace path is in the string
            if workspace_normalized in path_normalized:
                # Replace absolute path with relative path
                relative = path_normalized.replace(workspace_normalized, "")
                # Clean up leading/trailing separators
                relative = relative.lstrip("/")
                
                # If it already starts with backend/ or frontend/, return as is
                if relative.startswith(("backend/", "frontend/")):
                    return relative
                
                # If it's a backend file, add backend/ prefix
                if "/backend/" in path_normalized or path_normalized.endswith("/backend"):
                    return f"backend/{relative}" if relative else "backend"
                
                # If it's a frontend file, add frontend/ prefix
                if "/frontend/" in path_normalized or path_normalized.endswith("/frontend"):
                    return f"frontend/{relative}" if relative else "frontend"
                
                return relative if relative else "."
        except Exception:
            # If path shortening fails, return original
            pass

        return path_str

    def _shorten_logger_name(self, name: str) -> str:
        """Shorten logger names for cleaner output."""
        # Shorten common logger names
        if name == "uvicorn.error":
            return "uvicorn"
        if name == "uvicorn.access":
            return "uvicorn.access"
        if name.startswith("watchfiles"):
            return "watchfiles"
        if name.startswith("app."):
            # Keep app.* loggers as-is, they're already short
            return name
        # For other loggers, keep the last part if it has dots
        if "." in name:
            parts = name.split(".")
            # Keep last 2 parts for context
            return ".".join(parts[-2:])
        return name

    def format(self, record: logging.LogRecord) -> str:
        """Format log record, shortening paths in the message and exception info."""
        # Shorten logger name before formatting
        original_name = record.name
        record.name = self._shorten_logger_name(record.name)
        
        try:
            # Format the base message (this will call formatException if needed)
            message = super().format(record)
            
            # Shorten paths in the final message (including exception traceback)
            message = self._shorten_path(message)
        finally:
            # Restore original name in case it's used elsewhere
            record.name = original_name
        
        return message

    def formatException(self, ei) -> str:
        """Format exception with shortened paths."""
        import traceback

        exc_text = traceback.format_exception(*ei)
        result = []
        for line in exc_text:
            shortened = self._shorten_path(line)
            result.append(shortened)
        return "".join(result)


class PathShorteningFilter(logging.Filter):
    """Filter that shortens paths in log records before they're formatted."""
    
    def __init__(self, workspace_root: Path):
        """Initialize with workspace root for path shortening."""
        super().__init__()
        self.workspace_root = workspace_root
        self.workspace_str = str(workspace_root)
        self.workspace_normalized = self.workspace_str.replace("\\", "/")
    
    def _shorten_path(self, text: str) -> str:
        """Shorten paths in text."""
        if not text:
            return text
        try:
            text_normalized = text.replace("\\", "/")
            if self.workspace_normalized in text_normalized:
                relative = text_normalized.replace(self.workspace_normalized, "")
                relative = relative.lstrip("/")
                if relative.startswith(("backend/", "frontend/")):
                    return relative
                if "/backend/" in text_normalized or text_normalized.endswith("/backend"):
                    return f"backend/{relative}" if relative else "backend"
                if "/frontend/" in text_normalized or text_normalized.endswith("/frontend"):
                    return f"frontend/{relative}" if relative else "frontend"
                return relative if relative else "."
        except Exception:
            pass
        return text
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Process log record to shorten paths in the message."""
        # Shorten paths in the message
        if hasattr(record, 'msg') and record.msg:
            if isinstance(record.msg, str):
                record.msg = self._shorten_path(record.msg)
            elif isinstance(record.msg, (tuple, list)):
                # Handle formatted messages with args - convert to string and process
                record.msg = self._shorten_path(str(record.msg))
        # Also process args if they contain paths (like in formatted strings)
        if hasattr(record, 'args') and record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(self._shorten_path(arg))
                elif isinstance(arg, (list, tuple)):
                    # Handle lists/tuples that might contain paths (like directory lists)
                    processed = []
                    for item in arg:
                        if isinstance(item, str):
                            processed.append(self._shorten_path(item))
                        else:
                            processed.append(item)
                    new_args.append(type(arg)(processed))  # Preserve list or tuple type
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        # Also process the formatted message if it exists (after formatting)
        if hasattr(record, 'message') and record.message:
            record.message = self._shorten_path(record.message)
        return True


def configure_logging(formatter: logging.Formatter | None = None) -> None:
    """Configure all loggers to use the short path formatter."""
    if formatter is None:
        formatter = ShortPathFormatter(
            "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
        )
    
    # Get workspace root from formatter
    workspace_root = formatter.workspace_root if isinstance(formatter, ShortPathFormatter) else ShortPathFormatter._detect_workspace_root()
    
    # Create filter to shorten paths
    path_filter = PathShorteningFilter(workspace_root)
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(path_filter)  # Add filter to process paths before formatting
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.addFilter(path_filter)  # Also add filter to root logger
    
    # Configure specific loggers that might bypass root logger
    # These loggers are used by uvicorn and watchfiles
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "watchfiles", "watchfiles.main"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.addFilter(path_filter)  # Add filter to each logger
        logger.propagate = False  # Prevent double logging to root
