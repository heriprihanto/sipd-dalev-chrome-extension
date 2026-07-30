"""Titik masuk aplikasi FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import __version__
from .api import router
from .config import settings
from .db import engine, init_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("dalev-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.create_tables:
        try:
            init_db()
            log.info(
                "Tabel siap: %s, %s, %s",
                settings.table_program,
                settings.table_subkegiatan,
                settings.table_meta,
            )
        except Exception:
            # API tetap hidup supaya /health bisa menunjukkan masalahnya.
            log.exception("Gagal menyiapkan tabel database")
    yield


app = FastAPI(
    title="SIPD DALEV Realisasi API",
    description=(
        "Menyimpan hasil unduhan realisasi kinerja Program dan Subkegiatan "
        "dari SIPD DALEV ke PostgreSQL."
    ),
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.daftar_cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health() -> dict[str, object]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok, pesan = True, None
    except Exception as exc:  # noqa: BLE001
        db_ok, pesan = False, str(exc)

    return {
        "status": "ok" if db_ok else "degraded",
        "versi": __version__,
        "database": settings.postgres_db,
        "schema": settings.postgres_schema,
        "database_terhubung": db_ok,
        "pesan": pesan,
    }


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
