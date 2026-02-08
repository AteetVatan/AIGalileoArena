"""Load versioned JSON dataset files into Postgres at startup."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from collections import defaultdict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .db.repository import Repository

logger = logging.getLogger(__name__)

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"


def _get_highest_version_files(json_files: list[Path]) -> list[Path]:
    """Group files by base name and return only the highest version for each group.
    
    Example: ['climate_v1.json', 'climate_v2.json'] -> ['climate_v2.json']
    """
    # Pattern to extract base name and version from filename like "climate_v2.json"
    pattern = re.compile(r"^(.+)_v(\d+)\.json$")
    
    # Group files by base name
    groups: dict[str, list[tuple[int, Path]]] = defaultdict(list)
    
    for json_file in json_files:
        match = pattern.match(json_file.name)
        if match:
            base_name = match.group(1)
            version = int(match.group(2))
            groups[base_name].append((version, json_file))
    
    # For each group, return only the file with the highest version
    result = []
    for base_name, versions in groups.items():
        versions.sort(key=lambda x: x[0], reverse=True)  # Sort by version desc
        highest_version, highest_file = versions[0]
        result.append(highest_file)
        if len(versions) > 1:
            skipped = [f"{base_name}_v{v}.json" for v, _ in versions[1:]]
            logger.info(
                "Skipping lower version files for %s (v%d exists): %s",
                base_name, highest_version, ", ".join(skipped)
            )
    
    return sorted(result)  # Sort for consistent processing order


async def load_all_datasets(session: AsyncSession) -> None:
    repo = Repository(session)

    if not DATASET_DIR.exists():
        logger.warning("dataset dir missing: %s", DATASET_DIR.name)
        return

    all_json_files = sorted(DATASET_DIR.glob("*_v*.json"))
    json_files_to_process = _get_highest_version_files(all_json_files)

    for json_file in json_files_to_process:
        # Use a savepoint for each dataset so one failure doesn't rollback all previous work
        savepoint = await session.begin_nested()
        try:
            await _load_one(repo, json_file)
            await savepoint.commit()
        except IntegrityError:
            # Rollback just this savepoint and continue with next dataset
            await savepoint.rollback()
            logger.warning("Dataset from %s already exists, skipping.", json_file.name)
        except Exception:
            # Rollback this savepoint and continue
            await savepoint.rollback()
            logger.exception("failed to load %s", json_file.name)

    await repo.commit()
    logger.info("Dataset loading complete.")


def _extract_version_from_filename(filename: str) -> str:
    """Extract version number from filename like 'climate_v2.json' -> '2'."""
    pattern = re.compile(r"_v(\d+)\.json$")
    match = pattern.search(filename)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract version from filename: {filename}")


async def _load_one(repo: Repository, path: Path) -> None:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    dataset_id = data["id"]
    # Extract version from filename (e.g., "climate_v2.json" -> "2")
    new_version = _extract_version_from_filename(path.name)
    
    # Check if dataset exists and compare versions
    existing_dataset = await repo.get_dataset(dataset_id)
    if existing_dataset is not None:
        if existing_dataset.version == new_version:
            logger.info("dataset %s (version %s) already loaded, skipping.", dataset_id, new_version)
            return
        else:
            # Version changed - delete old dataset and recreate
            logger.info(
                "dataset %s version changed (%s -> %s), updating...",
                dataset_id, existing_dataset.version, new_version
            )
            await repo.delete_dataset(dataset_id)

    await repo.create_dataset(
        dataset_id=dataset_id,
        version=new_version,
        description=data.get("description", ""),
        meta_json=data.get("meta", {}),
    )

    for case in data.get("cases", []):
        evidence = [
            {"eid": ep["eid"], "summary": ep["summary"], "source": ep["source"], "date": ep["date"]}
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

    logger.info("Loaded dataset %s (version %s, %d cases).", dataset_id, new_version, len(data.get("cases", [])))
