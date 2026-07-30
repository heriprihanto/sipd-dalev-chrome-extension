"""Rute REST API."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlmodel import Session

from . import service
from .config import settings
from .db import get_session
from .models import JenisData, StatusJob
from .schemas import (
    DaftarParameterRealisasi,
    HasilKirimBaris,
    HasilKirimRealisasi,
    IngestSekali,
    JobBaru,
    KirimBaris,
    KirimRealisasi,
    KonfigurasiPublik,
    RingkasanJob,
    SelesaikanJob,
)


def wajib_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    """Autentikasi sederhana; nonaktif kalau API_KEY di .env kosong."""
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key tidak valid.",
        )


SesiDb = Annotated[Session, Depends(get_session)]

router = APIRouter(prefix="/api/v1", dependencies=[Depends(wajib_api_key)])


def _job_atau_404(session: Session, job_id: UUID):
    try:
        return service.ambil_job(session, job_id)
    except service.JobTidakDitemukan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} tidak ditemukan.",
        ) from None


@router.get("/config", response_model=KonfigurasiPublik)
def konfigurasi() -> KonfigurasiPublik:
    """Nilai bawaan server; dipakai extension sebagai fallback."""
    return KonfigurasiPublik(
        tahun_anggaran=settings.tahun_anggaran,
        kode_pemda=settings.kode_pemda,
        tabel={
            "program": settings.table_program,
            "subkegiatan": settings.table_subkegiatan,
            "meta": settings.table_meta,
            "jobs": settings.table_jobs,
        },
        butuh_api_key=bool(settings.api_key),
        simpan_raw=settings.store_raw,
    )


# --------------------------------------------------------------------- #
# Unggah bertahap: dipakai extension supaya tiap halaman DataTable
# langsung tersimpan dan progres terlihat.
# --------------------------------------------------------------------- #


@router.post("/jobs", response_model=RingkasanJob, status_code=status.HTTP_201_CREATED)
def mulai_job(permintaan: JobBaru, session: SesiDb) -> Any:
    return service.buat_job(session, permintaan)


@router.post("/jobs/{job_id}/rows", response_model=HasilKirimBaris)
def kirim_baris(job_id: UUID, permintaan: KirimBaris, session: SesiDb) -> Any:
    job = _job_atau_404(session, job_id)
    if StatusJob(job.status) != StatusJob.berjalan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job sudah berstatus {job.status}, tidak menerima baris baru.",
        )

    tersimpan = service.simpan_baris(session, job, permintaan.data)
    return HasilKirimBaris(
        job_id=job.job_id,
        diterima=len(permintaan.data),
        tersimpan=tersimpan,
        total_diterima=job.jumlah_baris_diterima,
        total_tersimpan=job.jumlah_baris_tersimpan,
    )


@router.post("/jobs/{job_id}/finish", response_model=RingkasanJob)
def selesaikan_job(job_id: UUID, permintaan: SelesaikanJob, session: SesiDb) -> Any:
    job = _job_atau_404(session, job_id)
    return service.selesaikan_job(session, job, permintaan)


@router.get("/jobs", response_model=list[RingkasanJob])
def riwayat_job(
    session: SesiDb,
    jenis_data: JenisData | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Any:
    return service.daftar_job(
        session, jenis_data=jenis_data, limit=limit, offset=offset
    )


@router.get("/jobs/{job_id}", response_model=RingkasanJob)
def detail_job(job_id: UUID, session: SesiDb) -> Any:
    return _job_atau_404(session, job_id)


# --------------------------------------------------------------------- #
# Unggah sekali jalan (mis. mengirim ulang file JSON hasil unduhan lama)
# --------------------------------------------------------------------- #


@router.post("/ingest", response_model=RingkasanJob, status_code=status.HTTP_201_CREATED)
def ingest(permintaan: IngestSekali, session: SesiDb) -> Any:
    try:
        return service.ingest_sekali(session, permintaan)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menyimpan data: {exc}",
        ) from exc


# --------------------------------------------------------------------- #
# Pembacaan data
# --------------------------------------------------------------------- #


@router.get("/data/{jenis}")
def baca_data(
    jenis: JenisData,
    session: SesiDb,
    tahun: int | None = None,
    kodepemda: str | None = None,
    kodeskpd: str | None = None,
    kodeprogram: str | None = None,
    kodesubkegiatan: str | None = None,
    row_type: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    total, baris = service.cari_baris(
        session,
        jenis,
        tahun=tahun,
        kodepemda=kodepemda,
        kodeskpd=kodeskpd,
        kodeprogram=kodeprogram,
        kodesubkegiatan=kodesubkegiatan,
        row_type=row_type,
        limit=limit,
        offset=offset,
    )
    return {"total": total, "limit": limit, "offset": offset, "data": baris}


@router.get("/statistik/{jenis}")
def statistik(jenis: JenisData, session: SesiDb) -> dict[str, Any]:
    if jenis == JenisData.realisasi_keuangan:
        return service.statistik_realisasi(session)
    return service.statistik(session, jenis)


# --------------------------------------------------------------------- #
# Realisasi keuangan per indikator output
# --------------------------------------------------------------------- #


@router.get("/realisasi-keuangan/parameter", response_model=DaftarParameterRealisasi)
def parameter_realisasi(
    session: SesiDb,
    tahun: int | None = None,
    kodepemda: str | None = None,
    kodeskpd: str | None = None,
    hanya_belum: bool = True,
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
) -> Any:
    """Daftar parameter POST `f=load_realisasi` dari baris output subkegiatan."""
    total, data = service.parameter_realisasi(
        session,
        tahun=tahun,
        kodepemda=kodepemda,
        kodeskpd=kodeskpd,
        hanya_belum=hanya_belum,
        limit=limit,
        offset=offset,
    )
    return DaftarParameterRealisasi(
        total=total, limit=limit, offset=offset, data=data
    )


@router.post("/jobs/{job_id}/realisasi", response_model=HasilKirimRealisasi)
def kirim_realisasi(job_id: UUID, permintaan: KirimRealisasi, session: SesiDb) -> Any:
    job = _job_atau_404(session, job_id)
    if StatusJob(job.status) != StatusJob.berjalan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job sudah berstatus {job.status}, tidak menerima hasil baru.",
        )

    berhasil = service.simpan_realisasi(session, job, permintaan.data)
    return HasilKirimRealisasi(
        job_id=job.job_id,
        diterima=len(permintaan.data),
        berhasil=berhasil,
        total_diterima=job.jumlah_baris_diterima,
        total_tersimpan=job.jumlah_baris_tersimpan,
    )


@router.get("/realisasi-keuangan")
def baca_realisasi(
    session: SesiDb,
    tahun: int | None = None,
    kodepemda: str | None = None,
    kodeskpd: str | None = None,
    kodesubkegiatan: str | None = None,
    status_hasil: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    total, baris = service.cari_realisasi(
        session,
        tahun=tahun,
        kodepemda=kodepemda,
        kodeskpd=kodeskpd,
        kodesubkegiatan=kodesubkegiatan,
        status_hasil=status_hasil,
        limit=limit,
        offset=offset,
    )
    return {"total": total, "limit": limit, "offset": offset, "data": baris}
