"""Load versioned JSON dataset files into Postgres at startup."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from .db.repository import Repository

logger = logging.getLogger(__name__)

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"


def _get_relative_path(path: Path) -> str:
    """Convert absolute path to relative path for logging."""
    try:
        # Try to find workspace root by navigating up from current file
        current = Path(__file__).resolve()
        workspace_root = None
        while current.parent != current:
            if (current / "backend").exists() and (current / "frontend").exists():
                workspace_root = current
                break
            current = current.parent
        
        if workspace_root:
            return str(path.relative_to(workspace_root))
        
        # Fallback: relative to backend directory
        backend_dir = Path(__file__).resolve().parent.parent.parent
        if backend_dir.name == "backend" and backend_dir.parent.exists():
            return str(path.relative_to(backend_dir.parent))
        return str(path.relative_to(backend_dir))
    except (ValueError, AttributeError):
        # If relative path calculation fails, return just the name
        return path.name


async def load_all_datasets(session: AsyncSession) -> None:
    """Scan datasets/ for JSON files and persist any that are missing."""
    repo = Repository(session)

    if not DATASET_DIR.exists():
        logger.warning("Dataset directory not found: %s", _get_relative_path(DATASET_DIR))
        return

    for json_file in sorted(DATASET_DIR.glob("*_v*.json")):
        try:
            await _load_one(repo, json_file)
        except Exception:
            logger.exception("Failed to load dataset %s", json_file.name)

    await repo.commit()
    logger.info("Dataset loading complete.")


async def _load_one(repo: Repository, path: Path) -> None:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    dataset_id = data["id"]
    if await repo.dataset_exists(dataset_id):
        logger.info("Dataset %s already loaded, skipping.", dataset_id)
        return

    await repo.create_dataset(
        dataset_id=dataset_id,
        version=data.get("version", "1.0"),
        description=data.get("description", ""),
        meta_json=data.get("meta", {}),
    )

    for case in data.get("cases", []):
        evidence = [
            {
                "eid": ep["eid"],
                "summary": ep["summary"],
                "source": ep["source"],
                "date": ep["date"],
            }
            for ep in case.get("evidence_packets", [])
        ]
        await repo.create_dataset_case(
            dataset_id=dataset_id,
            case_id=case["case_id"],
            topic=case["topic"],
            claim=case["claim"],
            pressure_score=case.get("pressure_score", 5),
            label=case["label"],
            evidence_json=evidence,
        )

    logger.info(
        "Loaded dataset %s (%d cases).",
        dataset_id,
        len(data.get("cases", [])),
    )
