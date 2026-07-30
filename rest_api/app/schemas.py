"""Skema request/response API."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from .models import JenisData, ModeSimpan, StatusJob


class InfoTahap(BaseModel):
    """Bagian `jobs_info` pada respons DataTable SIPD."""

    tahap_renstra: str | None = None
    tahap_rkpd: str | None = None
    tgl_tarik_renstra: str | None = None
    tgl_tarik_rkpd: str | None = None


class JobBaru(BaseModel):
    """Dibuat extension sebelum halaman pertama diunggah."""

    jenis_data: JenisData
    tahun: int | None = None
    kodepemda: str | None = None
    kodeskpd: str | None = None
    perangkat_daerah: str | None = None
    total_baris_server: int | None = None
    mode: ModeSimpan = ModeSimpan.replace
    sumber_url: str | None = None


class KirimBaris(BaseModel):
    """Satu halaman DataTable (baris JSON apa adanya)."""

    data: list[dict[str, Any]] = Field(default_factory=list)


class SelesaikanJob(BaseModel):
    lengkap: bool = True
    status: StatusJob = StatusJob.selesai
    catatan: str | None = None
    jobs_info: InfoTahap | None = None


class IngestSekali(BaseModel):
    """Unggah seluruh hasil unduhan dalam satu permintaan.

    Bentuknya mengikuti file JSON yang dihasilkan extension supaya file lama
    bisa dikirim ulang tanpa diubah.
    """

    jenis_data: JenisData
    tahun: int | None = None
    kodepemda: str | None = None
    kodeskpd: str | None = None
    perangkat_daerah: str | None = None
    total_baris_server: int | None = None
    lengkap: bool = True
    mode: ModeSimpan = ModeSimpan.replace
    sumber_url: str | None = None
    jobs_info: InfoTahap | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)


class ParameterRealisasi(BaseModel):
    """Parameter form POST `f=tarik_realisasi_keuangan` untuk satu subkegiatan.

    `kodepemda` tidak dikirim ke SIPD, hanya dipakai sebagai bagian kunci di
    database.
    """

    kodesubkegiatan: str | None = None
    kodekegiatan: str | None = None
    kodeprogram: str | None = None
    kodeskpd: str | None = None
    tahun: int | None = None
    kodepemda: str | None = None


class HasilRealisasi(BaseModel):
    """Satu hasil penarikan: parameter yang dipakai + respons SIPD."""

    parameter: ParameterRealisasi
    respons: Any | None = None
    status_http: int | None = None
    status: str = "ok"
    catatan: str | None = None


class KirimRealisasi(BaseModel):
    data: list[HasilRealisasi] = Field(default_factory=list)


class HasilKirimRealisasi(BaseModel):
    job_id: UUID
    diterima: int
    berhasil: int
    total_diterima: int
    total_tersimpan: int


class DaftarParameterRealisasi(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[ParameterRealisasi]


class RingkasanJob(BaseModel):
    job_id: UUID
    jenis_data: JenisData
    tahun: int
    kodepemda: str
    kodeskpd: str | None
    perangkat_daerah: str | None
    mode: ModeSimpan
    status: StatusJob
    lengkap: bool
    total_baris_server: int | None
    jumlah_baris_diterima: int
    jumlah_baris_tersimpan: int
    jumlah_baris_dihapus: int
    catatan: str | None
    dimulai_pada: datetime
    diperbarui_pada: datetime
    selesai_pada: datetime | None


class HasilKirimBaris(BaseModel):
    job_id: UUID
    diterima: int
    tersimpan: int
    total_diterima: int
    total_tersimpan: int


class KonfigurasiPublik(BaseModel):
    tahun_anggaran: int
    kode_pemda: str
    tabel: dict[str, str]
    butuh_api_key: bool
    simpan_raw: bool
