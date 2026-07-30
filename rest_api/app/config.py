"""Konfigurasi aplikasi, seluruhnya dibaca dari rest_api/.env."""

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_server: str = "127.0.0.1"
    postgres_db: str = "db_sipd_dalev"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_schema: str = "public"

    table_program: str = "dalev_realisasi_program"
    table_subkegiatan: str = "dalev_realisasi_subkegiatan"
    # Tahap & tanggal tarik data yang menyertai respons DataTable.
    table_meta: str = "dalev_jobs_info"
    # Riwayat eksekusi tombol Download di extension.
    table_jobs: str = "dalev_download_jobs"

    # Nilai bawaan kalau extension tidak mengirim tahun/kodepemda.
    tahun_anggaran: int = 2026
    kode_pemda: str = "3376"

    api_key: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "https://sipd.kemendagri.go.id"

    create_tables: bool = True
    db_echo: bool = False
    # Simpan juga baris JSON asli ke kolom `raw` (memperbesar ukuran tabel).
    store_raw: bool = False

    @property
    def sqlalchemy_dsn(self) -> str:
        """DSN psycopg3 (driver `psycopg`, bukan `psycopg2`)."""
        return (
            "postgresql+psycopg://"
            f"{quote_plus(self.postgres_user)}:{quote_plus(self.postgres_password)}"
            f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def daftar_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
