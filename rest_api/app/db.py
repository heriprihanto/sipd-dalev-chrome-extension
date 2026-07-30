"""Engine, sesi, dan penyiapan skema database (psycopg3)."""

import logging
from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from .config import settings

log = logging.getLogger("dalev-api")

engine = create_engine(
    settings.sqlalchemy_dsn,
    echo=settings.db_echo,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


def _tambah_kolom_baru() -> list[str]:
    """Menambahkan kolom yang belum ada pada tabel yang sudah terbentuk.

    `create_all` melewati tabel yang sudah ada, sehingga tabel bawaan project
    SIPD_DALEV tidak otomatis mendapat kolom tambahan (mis. `job_id`, `raw`,
    `renstra_real_kin`). Semua kolom tambahan bersifat nullable, jadi
    penambahannya aman dijalankan berulang.
    """
    inspector = inspect(engine)
    perubahan: list[str] = []

    with engine.begin() as conn:
        for tabel in SQLModel.metadata.sorted_tables:
            skema = tabel.schema or settings.postgres_schema
            if not inspector.has_table(tabel.name, schema=skema):
                continue

            ada = {
                k["name"] for k in inspector.get_columns(tabel.name, schema=skema)
            }
            for kolom in tabel.columns:
                if kolom.name in ada or kolom.primary_key or not kolom.nullable:
                    continue
                tipe = kolom.type.compile(engine.dialect)
                conn.execute(
                    text(
                        f'ALTER TABLE "{skema}"."{tabel.name}" '
                        f'ADD COLUMN IF NOT EXISTS "{kolom.name}" {tipe}'
                    )
                )
                perubahan.append(f"{tabel.name}.{kolom.name}")

    return perubahan


def init_db() -> None:
    """Membuat schema, tabel, dan kolom yang belum ada."""
    from . import models  # noqa: F401 - memastikan metadata terisi

    if settings.postgres_schema and settings.postgres_schema != "public":
        with engine.begin() as conn:
            conn.execute(
                text(f'CREATE SCHEMA IF NOT EXISTS "{settings.postgres_schema}"')
            )

    SQLModel.metadata.create_all(engine)

    if perubahan := _tambah_kolom_baru():
        log.info("Kolom baru ditambahkan: %s", ", ".join(perubahan))


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
