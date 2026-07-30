"""Logika penyimpanan data unduhan DALEV."""

from functools import lru_cache
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session

from .config import settings
from .models import (
    JENIS_DATATABLE,
    PARAMETER_REALISASI,
    DownloadJob,
    JenisData,
    JobsInfo,
    ModeSimpan,
    RealisasiKeuangan,
    StatusJob,
    kunci_baris,
    model_baris,
    sekarang,
)
from .parsing import buang_duplikat, normalisasi_baris
from .schemas import (
    HasilRealisasi,
    IngestSekali,
    InfoTahap,
    JobBaru,
    SelesaikanJob,
)

# Jumlah baris per statement INSERT ... ON CONFLICT.
UKURAN_BATCH = 500


class JobTidakDitemukan(Exception):
    pass


@lru_cache
def _statement_upsert(jenis: JenisData) -> Any:
    """INSERT ... ON CONFLICT DO UPDATE untuk satu jenis data.

    Statement dibangun sekali lalu dipakai berulang dengan daftar parameter,
    sehingga SQLAlchemy dan psycopg bisa memakai bentuk executemany.
    """
    tabel = model_baris(jenis).__table__
    kunci = set(kunci_baris(jenis))
    stmt = pg_insert(tabel)
    kolom_update = {
        c.name: stmt.excluded[c.name]
        for c in tabel.columns
        if c.name not in kunci and c.name not in {"id", "fetched_at"}
    }
    return stmt.on_conflict_do_update(
        index_elements=list(kunci_baris(jenis)),
        set_=kolom_update,
    )


def buat_job(session: Session, permintaan: JobBaru) -> DownloadJob:
    job = DownloadJob(
        jenis_data=permintaan.jenis_data,
        tahun=permintaan.tahun or settings.tahun_anggaran,
        kodepemda=permintaan.kodepemda or settings.kode_pemda,
        kodeskpd=permintaan.kodeskpd or None,
        perangkat_daerah=permintaan.perangkat_daerah,
        total_baris_server=permintaan.total_baris_server,
        mode=permintaan.mode,
        sumber_url=permintaan.sumber_url,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def ambil_job(session: Session, job_id: UUID) -> DownloadJob:
    job = session.execute(
        select(DownloadJob).where(DownloadJob.job_id == job_id)
    ).scalar_one_or_none()
    if job is None:
        raise JobTidakDitemukan(str(job_id))
    return job


def _potong(baris: list[dict[str, Any]], ukuran: int):
    for i in range(0, len(baris), ukuran):
        yield baris[i : i + ukuran]


def simpan_baris(
    session: Session,
    job: DownloadJob,
    data: list[dict[str, Any]],
) -> int:
    """Upsert baris DataTable ke tabel program/subkegiatan.

    Kunci konflik memakai kode natural SIPD (lihat `KUNCI_PER_JENIS`), jadi
    unduhan ulang memperbarui baris yang sama tanpa menduplikasi.
    """
    if not data:
        return 0

    jenis = JenisData(job.jenis_data)
    model = model_baris(jenis)
    tabel = model.__table__
    waktu = sekarang()

    baris_siap = [
        normalisasi_baris(
            satu,
            jenis=jenis,
            tahun=job.tahun,
            kodepemda=job.kodepemda,
            simpan_raw=settings.store_raw,
        )
        for satu in data
        if isinstance(satu, dict)
    ]
    for satu in baris_siap:
        satu["job_id"] = job.job_id
        satu["fetched_at"] = waktu
        satu["updated_at"] = waktu

    baris_siap = buang_duplikat(baris_siap, jenis)
    if not baris_siap:
        return 0

    # Semua dict harus punya kunci yang sama supaya satu statement bisa
    # dijalankan gaya executemany (jauh lebih cepat daripada satu statement
    # raksasa berisi ratusan baris).
    kolom_isi = [c.name for c in tabel.columns if c.name != "id"]
    baris_lengkap = [{nama: satu.get(nama) for nama in kolom_isi} for satu in baris_siap]

    for bagian in _potong(baris_lengkap, UKURAN_BATCH):
        session.execute(_statement_upsert(jenis), bagian)

    job.jumlah_baris_diterima += len(data)
    job.jumlah_baris_tersimpan += len(baris_lengkap)
    job.diperbarui_pada = waktu
    session.add(job)
    session.commit()
    session.refresh(job)
    return len(baris_lengkap)


def simpan_info_tahap(
    session: Session,
    *,
    tahun: int,
    kodepemda: str,
    info: InfoTahap | None,
    records_total: int | None,
) -> None:
    """Upsert `jobs_info` dari respons DataTable (tahap & tanggal tarik data)."""
    if info is None and records_total is None:
        return

    info = info or InfoTahap()
    nilai = {
        "tahun": tahun,
        "kodepemda": kodepemda,
        "tahap_renstra": info.tahap_renstra,
        "tahap_rkpd": info.tahap_rkpd,
        "tgl_tarik_renstra": info.tgl_tarik_renstra,
        "tgl_tarik_rkpd": info.tgl_tarik_rkpd,
        "records_total": records_total,
        "fetched_at": sekarang(),
    }
    stmt = pg_insert(JobsInfo.__table__).values(nilai)
    stmt = stmt.on_conflict_do_update(
        index_elements=["tahun", "kodepemda"],
        set_={k: stmt.excluded[k] for k in nilai if k not in {"tahun", "kodepemda"}},
    )
    session.execute(stmt)
    session.commit()


def cakupan_baris(session: Session, job: DownloadJob) -> list[tuple[int, str]]:
    """Pasangan (tahun, kodepemda) yang benar-benar tertulis oleh job ini.

    Tahun dan kode pemda diambil dari isi baris SIPD, bukan dari parameter yang
    dikirim extension, sehingga keduanya bisa berbeda (mis. filter dashboard
    belum terbaca). Pembersihan dan pencatatan tahap memakai cakupan nyata ini.
    """
    tabel = model_baris(JenisData(job.jenis_data)).__table__
    baris = session.execute(
        select(tabel.c.tahun, tabel.c.kodepemda)
        .where(tabel.c.job_id == job.job_id)
        .distinct()
    ).all()
    return [(int(t), str(k)) for t, k in baris]


def _hapus_baris_kadaluarsa(
    session: Session,
    job: DownloadJob,
    cakupan: list[tuple[int, str]],
) -> int:
    """Menghapus baris cakupan sama yang tidak ikut pada job ini.

    Cakupan = tahun + kodepemda (+ kodeskpd bila unduhan difilter per OPD).
    Kalau unduhan mencakup semua OPD, seluruh baris tahun+pemda dibersihkan.
    """
    tabel = model_baris(JenisData(job.jenis_data)).__table__
    dihapus = 0

    for tahun, kodepemda in cakupan:
        stmt = delete(tabel).where(
            tabel.c.tahun == tahun,
            tabel.c.kodepemda == kodepemda,
            tabel.c.job_id.is_distinct_from(job.job_id),
        )
        if job.kodeskpd:
            stmt = stmt.where(tabel.c.kodeskpd == job.kodeskpd)
        dihapus += session.execute(stmt).rowcount or 0

    return dihapus


def selesaikan_job(
    session: Session,
    job: DownloadJob,
    permintaan: SelesaikanJob,
) -> DownloadJob:
    """Menutup job; pada mode replace, baris versi lama dihapus.

    Penghapusan hanya dilakukan bila unduhan dinyatakan lengkap, supaya
    unduhan yang dibatalkan di tengah jalan tidak menghapus data valid.
    """
    # Penarikan realisasi keuangan bersifat menambah/memperbarui per indikator,
    # jadi tidak ada pembersihan cakupan maupun pencatatan tahap.
    datatable = JenisData(job.jenis_data) in JENIS_DATATABLE
    cakupan = (
        (cakupan_baris(session, job) or [(job.tahun, job.kodepemda)])
        if datatable
        else []
    )

    dihapus = 0
    if (
        datatable
        and permintaan.status == StatusJob.selesai
        and permintaan.lengkap
        and ModeSimpan(job.mode) == ModeSimpan.replace
    ):
        dihapus = _hapus_baris_kadaluarsa(session, job, cakupan)

    job.jumlah_baris_dihapus += dihapus
    job.lengkap = permintaan.lengkap
    job.status = permintaan.status
    job.catatan = permintaan.catatan
    job.diperbarui_pada = sekarang()
    job.selesai_pada = sekarang()
    session.add(job)
    session.commit()
    session.refresh(job)

    for tahun, kodepemda in cakupan:
        simpan_info_tahap(
            session,
            tahun=tahun,
            kodepemda=kodepemda,
            info=permintaan.jobs_info,
            records_total=job.total_baris_server or job.jumlah_baris_tersimpan,
        )
    return job


def ingest_sekali(session: Session, permintaan: IngestSekali) -> DownloadJob:
    """Buat job, simpan semua baris, lalu tutup job dalam satu panggilan."""
    job = buat_job(
        session,
        JobBaru(
            jenis_data=permintaan.jenis_data,
            tahun=permintaan.tahun,
            kodepemda=permintaan.kodepemda,
            kodeskpd=permintaan.kodeskpd,
            perangkat_daerah=permintaan.perangkat_daerah,
            total_baris_server=permintaan.total_baris_server or len(permintaan.data),
            mode=permintaan.mode,
            sumber_url=permintaan.sumber_url,
        ),
    )
    try:
        for bagian in _potong(permintaan.data, UKURAN_BATCH * 4):
            simpan_baris(session, job, bagian)
    except Exception as exc:  # noqa: BLE001 - status job harus tetap tercatat
        session.rollback()
        job = ambil_job(session, job.job_id)
        selesaikan_job(
            session,
            job,
            SelesaikanJob(lengkap=False, status=StatusJob.gagal, catatan=str(exc)),
        )
        raise

    return selesaikan_job(
        session,
        job,
        SelesaikanJob(
            lengkap=permintaan.lengkap,
            status=StatusJob.selesai,
            jobs_info=permintaan.jobs_info,
        ),
    )


# --------------------------------------------------------------------- #
# Realisasi keuangan per indikator output
# --------------------------------------------------------------------- #


def parameter_realisasi(
    session: Session,
    *,
    tahun: int | None = None,
    kodepemda: str | None = None,
    kodeskpd: str | None = None,
    hanya_belum: bool = True,
    limit: int = 500,
    offset: int = 0,
) -> tuple[int, list[dict[str, Any]]]:
    """Parameter POST `f=load_realisasi`, diambil dari baris output subkegiatan.

    `hanya_belum` melewati indikator yang responsnya sudah tersimpan, sehingga
    penarikan yang terputus bisa dilanjutkan tanpa mengulang dari awal.
    """
    sub = model_baris(JenisData.subkegiatan).__table__
    hasil = RealisasiKeuangan.__table__

    filter_ = [sub.c.row_type == "output"]
    if tahun is not None:
        filter_.append(sub.c.tahun == tahun)
    if kodepemda:
        filter_.append(sub.c.kodepemda == kodepemda)
    if kodeskpd:
        filter_.append(sub.c.kodeskpd == kodeskpd)

    if hanya_belum:
        sudah = (
            select(hasil.c.id)
            .where(
                hasil.c.tahun == sub.c.tahun,
                hasil.c.kodepemda == sub.c.kodepemda,
                hasil.c.kodeskpd == sub.c.kodeskpd,
                hasil.c.kodesubkegiatan == sub.c.kodesubkegiatan,
                hasil.c.kodesubkegiatan_indikator == sub.c.kodesubkegiatan_indikator,
                hasil.c.status == "ok",
            )
            .exists()
        )
        filter_.append(~sudah)

    total = session.execute(
        select(func.count()).select_from(sub).where(*filter_)
    ).scalar_one()

    kolom = [sub.c.kodepemda, *[sub.c[nama] for nama in PARAMETER_REALISASI]]
    baris = session.execute(
        select(*kolom)
        .where(*filter_)
        .order_by(sub.c.kodeskpd, sub.c.kodesubkegiatan, sub.c.id)
        .limit(limit)
        .offset(offset)
    ).all()

    return total, [dict(satu._mapping) for satu in baris]


def simpan_realisasi(
    session: Session,
    job: DownloadJob,
    data: list[HasilRealisasi],
) -> int:
    """Upsert hasil penarikan realisasi keuangan (satu baris per indikator)."""
    if not data:
        return 0

    tabel = RealisasiKeuangan.__table__
    waktu = sekarang()
    kolom_isi = [c.name for c in tabel.columns if c.name != "id"]

    per_kunci: dict[tuple, dict[str, Any]] = {}
    for satu in data:
        p = satu.parameter
        nilai: dict[str, Any] = {
            "tahun": p.tahun or job.tahun,
            "kodepemda": p.kodepemda or job.kodepemda,
            "kodeskpd": p.kodeskpd or "",
            "kodesubkegiatan": p.kodesubkegiatan or "",
            "kodesubkegiatan_indikator": p.kodesubkegiatan_indikator or "",
            "kodebidang": p.kodebidang,
            "kodeprogram": p.kodeprogram,
            "kodekegiatan": p.kodekegiatan,
            "idoutcome": p.idoutcome,
            "idoutput": p.idoutput,
            "respons": satu.respons,
            "status_http": satu.status_http,
            "status": satu.status,
            "catatan": satu.catatan,
            "job_id": job.job_id,
            "fetched_at": waktu,
            "updated_at": waktu,
        }
        kunci = (
            nilai["tahun"],
            nilai["kodepemda"],
            nilai["kodeskpd"],
            nilai["kodesubkegiatan"],
            nilai["kodesubkegiatan_indikator"],
        )
        per_kunci[kunci] = {nama: nilai.get(nama) for nama in kolom_isi}

    stmt = pg_insert(tabel)
    kolom_update = {
        c.name: stmt.excluded[c.name]
        for c in tabel.columns
        if c.name
        not in {
            "id",
            "fetched_at",
            "tahun",
            "kodepemda",
            "kodeskpd",
            "kodesubkegiatan",
            "kodesubkegiatan_indikator",
        }
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=[
            "tahun",
            "kodepemda",
            "kodeskpd",
            "kodesubkegiatan",
            "kodesubkegiatan_indikator",
        ],
        set_=kolom_update,
    )

    baris = list(per_kunci.values())
    for bagian in _potong(baris, UKURAN_BATCH):
        session.execute(stmt, bagian)

    berhasil = sum(1 for satu in baris if satu.get("status") == "ok")
    job.jumlah_baris_diterima += len(data)
    job.jumlah_baris_tersimpan += berhasil
    job.diperbarui_pada = waktu
    session.add(job)
    session.commit()
    session.refresh(job)
    return berhasil


def cari_realisasi(
    session: Session,
    *,
    tahun: int | None = None,
    kodepemda: str | None = None,
    kodeskpd: str | None = None,
    kodesubkegiatan: str | None = None,
    status_hasil: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[Any]]:
    tabel = RealisasiKeuangan.__table__

    filter_ = []
    if tahun is not None:
        filter_.append(tabel.c.tahun == tahun)
    if kodepemda:
        filter_.append(tabel.c.kodepemda == kodepemda)
    if kodeskpd:
        filter_.append(tabel.c.kodeskpd == kodeskpd)
    if kodesubkegiatan:
        filter_.append(tabel.c.kodesubkegiatan == kodesubkegiatan)
    if status_hasil:
        filter_.append(tabel.c.status == status_hasil)

    total = session.execute(
        select(func.count()).select_from(tabel).where(*filter_)
    ).scalar_one()

    stmt = (
        select(RealisasiKeuangan)
        .where(*filter_)
        .order_by(tabel.c.kodeskpd, tabel.c.kodesubkegiatan, tabel.c.id)
        .limit(limit)
        .offset(offset)
    )
    return total, list(session.execute(stmt).scalars())


def statistik_realisasi(session: Session) -> dict[str, Any]:
    tabel = RealisasiKeuangan.__table__
    sub = model_baris(JenisData.subkegiatan).__table__

    ringkas = session.execute(
        select(
            func.count().label("jumlah_baris"),
            func.max(tabel.c.updated_at).label("terakhir_diperbarui"),
        ).select_from(tabel)
    ).one()
    per_status = session.execute(
        select(tabel.c.status, func.count())
        .select_from(tabel)
        .group_by(tabel.c.status)
    ).all()
    target = session.execute(
        select(func.count()).select_from(sub).where(sub.c.row_type == "output")
    ).scalar_one()

    return {
        "tabel": RealisasiKeuangan.__tablename__,
        "jumlah_indikator_output": target,
        "jumlah_baris": ringkas.jumlah_baris,
        "per_status": {nama or "(kosong)": jumlah for nama, jumlah in per_status},
        "terakhir_diperbarui": ringkas.terakhir_diperbarui,
    }


def daftar_job(
    session: Session,
    *,
    jenis_data: JenisData | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[DownloadJob]:
    stmt = select(DownloadJob).order_by(DownloadJob.dimulai_pada.desc())
    if jenis_data:
        stmt = stmt.where(DownloadJob.jenis_data == jenis_data)
    return list(session.execute(stmt.limit(limit).offset(offset)).scalars())


def cari_baris(
    session: Session,
    jenis: JenisData,
    *,
    tahun: int | None = None,
    kodepemda: str | None = None,
    kodeskpd: str | None = None,
    kodeprogram: str | None = None,
    kodesubkegiatan: str | None = None,
    row_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[Any]]:
    model = model_baris(jenis)
    tabel = model.__table__

    filter_ = []
    if tahun is not None:
        filter_.append(tabel.c.tahun == tahun)
    if kodepemda:
        filter_.append(tabel.c.kodepemda == kodepemda)
    if kodeskpd:
        filter_.append(tabel.c.kodeskpd == kodeskpd)
    if kodeprogram:
        filter_.append(tabel.c.kodeprogram == kodeprogram)
    if kodesubkegiatan:
        filter_.append(tabel.c.kodesubkegiatan == kodesubkegiatan)
    if row_type:
        filter_.append(tabel.c.row_type == row_type)

    total = session.execute(
        select(func.count()).select_from(tabel).where(*filter_)
    ).scalar_one()

    stmt = (
        select(model)
        .where(*filter_)
        .order_by(tabel.c.kodeskpd, tabel.c.nomor_urut, tabel.c.id)
        .limit(limit)
        .offset(offset)
    )
    return total, list(session.execute(stmt).scalars())


def statistik(session: Session, jenis: JenisData) -> dict[str, Any]:
    model = model_baris(jenis)
    tabel = model.__table__

    ringkas = session.execute(
        select(
            func.count().label("jumlah_baris"),
            func.count(func.distinct(tabel.c.kodeskpd)).label("jumlah_skpd"),
            func.max(tabel.c.updated_at).label("terakhir_diperbarui"),
        ).select_from(tabel)
    ).one()

    per_row_type = session.execute(
        select(tabel.c.row_type, func.count())
        .select_from(tabel)
        .group_by(tabel.c.row_type)
        .order_by(tabel.c.row_type)
    ).all()

    return {
        "jenis_data": jenis,
        "tabel": model.__tablename__,
        "jumlah_baris": ringkas.jumlah_baris,
        "jumlah_skpd": ringkas.jumlah_skpd,
        "per_row_type": {nama or "(kosong)": jumlah for nama, jumlah in per_row_type},
        "terakhir_diperbarui": ringkas.terakhir_diperbarui,
    }
