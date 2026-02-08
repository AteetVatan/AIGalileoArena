from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.datasets import router as datasets_router
from app.api.routes.runs import router as runs_router
from app.config import settings
from app.infra.db.session import init_db
from app.infra.logging_config import ShortPathFormatter, configure_logging

formatter = ShortPathFormatter(
    "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
)
configure_logging(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising database tables...")
    await init_db()

    logger.info("Loading datasets into Postgres...")
    from app.infra.db.session import async_session_factory
    from app.infra.dataset_loader import load_all_datasets

    async with async_session_factory() as session:
        await load_all_datasets(session)

    # wipe cache slots on startup so stale CACHE_RESULTS
    # changes don't serve outdated results
    from app.infra.db.repository import Repository

    async with async_session_factory() as session:
        repo = Repository(session)
        deleted = await repo.delete_all_cache_slots()
        await repo.commit()
        if deleted:
            logger.info("Cleared %d cached result slot(s) on startup.", deleted)

    # --- ML scoring model warm-up (optional) ---
    if settings.ml_scoring_enabled:
        try:
            from app.infra.ml.model_registry import ModelRegistry

            logger.info(
                "Loading ONNX ML scoring models from '%s' ...",
                settings.ml_models_dir,
            )
            ModelRegistry.warm_up()
            logger.info("ML scoring models ready (2 ONNX sessions).")
        except FileNotFoundError as e:
            logger.warning(
                "ML_SCORING_ENABLED=true but ONNX models not found in '%s/'. "
                "ML scoring will be disabled. Run the export script to enable: "
                "python -m scripts.export_onnx_models --output-dir %s",
                settings.ml_models_dir,
                settings.ml_models_dir,
            )
            # Disable ML scoring for this session
            settings.ml_scoring_enabled = False
        except Exception as e:
            logger.error(
                "Failed to load ML scoring models: %s. ML scoring will be disabled.",
                e,
                exc_info=True,
            )
            settings.ml_scoring_enabled = False

    logger.info("Galileo Arena ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Galileo Arena",
    description="Multi-model agentic debate evaluation platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets_router)
app.include_router(runs_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
