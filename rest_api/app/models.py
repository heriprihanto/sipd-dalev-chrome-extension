"""Tabel database (SQLModel).

Nama kolom mengikuti field JSON DataTable SIPD DALEV apa adanya, sama seperti
skema yang sudah dipakai project SIPD_DALEV, supaya tabel `dalev_realisasi_*`
yang sudah ada tetap bisa dipakai.

Baris program dan subkegiatan berasal dari respons dengan struktur yang sama
(hirarki bertingkat dibedakan `xstyle`), jadi kolomnya didefinisikan sekali di
`BarisDalevBase`. Yang berbeda hanya kunci uniknya:

* program     : tahun, kodepemda, kodeskpd, kodebidang, kodeprogram,
                idoutcome, kodeindikator_program
* subkegiatan : tahun, kodepemda, kodeskpd, kodesubkegiatan,
                kodesubkegiatan_indikator

Kolom kunci tidak boleh NULL supaya ON CONFLICT tetap bekerja pada baris induk
yang belum punya kode di tingkat bawah; nilai kosong ditulis sebagai "".
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Column, DateTime, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from .config import settings

SCHEMA = settings.postgres_schema

TIPE_ANGKA = Numeric()
TIPE_WAKTU = DateTime(timezone=True)


def sekarang() -> datetime:
    return datetime.now(timezone.utc)


def _pk_bigserial() -> Any:
    """Primary key bigserial; dibuat per kelas karena Column tidak bisa dibagi."""
    return Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )


class JenisData(str, Enum):
    program = "program"
    subkegiatan = "subkegiatan"
    # Penarikan detail realisasi keuangan per indikator output.
    realisasi_keuangan = "realisasi_keuangan"


# Jenis yang barisnya berasal dari DataTable (punya tabel baris sendiri).
JENIS_DATATABLE = (JenisData.program, JenisData.subkegiatan)


class ModeSimpan(str, Enum):
    # replace: setelah job selesai, baris cakupan sama dari unduhan sebelumnya
    # dihapus sehingga isi tabel persis seperti di SIPD.
    replace = "replace"
    # upsert: hanya menambah/memperbarui.
    upsert = "upsert"


class StatusJob(str, Enum):
    berjalan = "berjalan"
    selesai = "selesai"
    gagal = "gagal"
    dibatalkan = "dibatalkan"


class BarisDalevBase(SQLModel):
    """Kolom bersama tabel program dan subkegiatan (semua boleh NULL)."""

    # --- identitas hirarki ------------------------------------------------
    xstyle: str | None = Field(default=None, sa_type=Text)
    # Tingkat baris hasil terjemahan xstyle/DT_RowClass: bidang, program,
    # outcome, subkegiatan, output/indikator.
    row_type: str | None = Field(default=None, sa_type=Text, index=True)
    idperiode: str | None = Field(default=None, sa_type=Text)
    # Field "id" dari respons SIPD (bukan primary key tabel ini).
    id_sipd: str | None = Field(default=None, sa_type=Text)

    uraiskpd: str | None = Field(default=None, sa_type=Text)
    uraibidang: str | None = Field(default=None, sa_type=Text)
    uraiprogram: str | None = Field(default=None, sa_type=Text)
    uraioutcome: str | None = Field(default=None, sa_type=Text)
    uraiindikator_program: str | None = Field(default=None, sa_type=Text)
    kodekegiatan: str | None = Field(default=None, sa_type=Text)
    uraikegiatan: str | None = Field(default=None, sa_type=Text)
    idoutput: str | None = Field(default=None, sa_type=Text)
    uraioutput: str | None = Field(default=None, sa_type=Text)
    uraisubkegiatan: str | None = Field(default=None, sa_type=Text)
    uraisubkegiatan_indikator: str | None = Field(default=None, sa_type=Text)

    # --- deskripsi --------------------------------------------------------
    title: str | None = Field(default=None, sa_type=Text)
    indikator: str | None = Field(default=None, sa_type=Text)
    indikator_label: str | None = Field(default=None, sa_type=Text)
    satuan: str | None = Field(default=None, sa_type=Text)
    status: str | None = Field(default=None, sa_type=Text)
    tipe_data: str | None = Field(default=None, sa_type=Text)
    spm: str | None = Field(default=None, sa_type=Text)
    jenis: str | None = Field(default=None, sa_type=Text)
    keterangan: str | None = Field(default=None, sa_type=Text)
    baseline: str | None = Field(default=None, sa_type=Text)
    prosn: bool | None = Field(default=None)

    # --- kolom JSON -------------------------------------------------------
    lokasi: Any | None = Field(default=None, sa_type=JSONB)
    tag: Any | None = Field(default=None, sa_type=JSONB)
    valid: Any | None = Field(default=None, sa_type=JSONB)
    rakortek_tahun: Any | None = Field(default=None, sa_type=JSONB)
    pilihan_input: Any | None = Field(default=None, sa_type=JSONB)
    # Baris asli; hanya diisi bila STORE_RAW=true di .env.
    raw: Any | None = Field(default=None, sa_type=JSONB)

    total_indikator_program: int | None = Field(default=None)
    nomor_urut: int | None = Field(default=None)

    # --- target & realisasi ----------------------------------------------
    renstra_target_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    renstra_target_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    renstra_real_lalu_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    renstra_real_lalu_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    renstra_real_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    renstra_real_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    renstra_cap_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    renstra_cap_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)

    rkpd_target_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_target_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    apbd_target_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)

    rkpd_real_tw1_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_real_tw2_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_real_tw3_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_real_tw4_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_real_tw1_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_real_tw2_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_real_tw3_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_real_tw4_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_real_kin: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    rkpd_real_keu: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)

    realkeu_th_1: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    realkeu_th_2: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    realkeu_th_3: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    realkeu_th_4: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    realkeu_th_5: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)

    target_0: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    target_1: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    target_2: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    target_3: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    target_4: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    target_5: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    pagu_0: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    pagu_1: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    pagu_2: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    pagu_3: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    pagu_4: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)
    pagu_5: Decimal | None = Field(default=None, sa_type=TIPE_ANGKA)

    # --- jejak unduhan ----------------------------------------------------
    # Dipakai mode replace untuk mengenali baris dari unduhan sebelumnya.
    job_id: UUID | None = Field(default=None, index=True)
    fetched_at: datetime = Field(default_factory=sekarang, sa_type=TIPE_WAKTU)
    updated_at: datetime = Field(default_factory=sekarang, sa_type=TIPE_WAKTU)


class RealisasiProgram(BarisDalevBase, table=True):
    """Realisasi kinerja program (baris bidang, program, dan outcome)."""

    __tablename__ = settings.table_program
    __table_args__ = (
        UniqueConstraint(
            "tahun",
            "kodepemda",
            "kodeskpd",
            "kodebidang",
            "kodeprogram",
            "idoutcome",
            "kodeindikator_program",
            name=f"{settings.table_program}_uq",
        ),
        {"schema": SCHEMA},
    )

    id: int | None = _pk_bigserial()

    tahun: int = Field(index=True, nullable=False)
    kodepemda: str = Field(sa_type=Text, nullable=False)
    kodeskpd: str = Field(sa_type=Text, nullable=False)
    kodebidang: str = Field(sa_type=Text, nullable=False)
    kodeprogram: str = Field(sa_type=Text, nullable=False)
    idoutcome: str = Field(sa_type=Text, nullable=False)
    kodeindikator_program: str = Field(sa_type=Text, nullable=False)

    kodesubkegiatan: str | None = Field(default=None, sa_type=Text)
    kodesubkegiatan_indikator: str | None = Field(default=None, sa_type=Text)


class RealisasiSubkegiatan(BarisDalevBase, table=True):
    """Realisasi subkegiatan (baris subkegiatan dan indikator output)."""

    __tablename__ = settings.table_subkegiatan
    __table_args__ = (
        UniqueConstraint(
            "tahun",
            "kodepemda",
            "kodeskpd",
            "kodesubkegiatan",
            "kodesubkegiatan_indikator",
            name=f"{settings.table_subkegiatan}_uq",
        ),
        {"schema": SCHEMA},
    )

    id: int | None = _pk_bigserial()

    tahun: int = Field(index=True, nullable=False)
    kodepemda: str = Field(sa_type=Text, nullable=False)
    kodeskpd: str = Field(sa_type=Text, nullable=False)
    kodesubkegiatan: str = Field(sa_type=Text, nullable=False)
    kodesubkegiatan_indikator: str = Field(sa_type=Text, nullable=False)

    kodebidang: str | None = Field(default=None, sa_type=Text)
    kodeprogram: str | None = Field(default=None, sa_type=Text)
    idoutcome: str | None = Field(default=None, sa_type=Text)
    kodeindikator_program: str | None = Field(default=None, sa_type=Text)


class RealisasiKeuangan(SQLModel, table=True):
    """Hasil POST `f=tarik_realisasi_keuangan` untuk satu subkegiatan.

    Seluruh parameter permintaan menjadi kunci unik (ditambah `kodepemda` yang
    tidak dikirim ke SIPD tapi dibutuhkan agar data antar pemda tidak
    tertukar). Isi respons disimpan utuh di `respons` (jsonb) karena
    strukturnya ditentukan SIPD; kolom bertipe bisa ditambahkan belakangan
    tanpa kehilangan data.
    """

    __tablename__ = settings.table_realisasi
    __table_args__ = (
        UniqueConstraint(
            "tahun",
            "kodepemda",
            "kodeskpd",
            "kodeprogram",
            "kodekegiatan",
            "kodesubkegiatan",
            name=f"{settings.table_realisasi}_uq",
        ),
        {"schema": SCHEMA},
    )

    id: int | None = _pk_bigserial()

    # --- parameter permintaan (sekaligus kunci) ---------------------------
    tahun: int = Field(index=True, nullable=False)
    kodepemda: str = Field(sa_type=Text, nullable=False)
    kodeskpd: str = Field(sa_type=Text, nullable=False)
    kodeprogram: str = Field(sa_type=Text, nullable=False)
    kodekegiatan: str = Field(sa_type=Text, nullable=False)
    kodesubkegiatan: str = Field(sa_type=Text, nullable=False)

    # --- hasil ------------------------------------------------------------
    respons: Any | None = Field(default=None, sa_type=JSONB)
    status_http: int | None = Field(default=None)
    # "ok" bila respons tersimpan, "gagal" bila SIPD menolak permintaan.
    status: str | None = Field(default=None, sa_type=Text, index=True)
    catatan: str | None = Field(default=None, sa_type=Text)

    job_id: UUID | None = Field(default=None, index=True)
    fetched_at: datetime = Field(default_factory=sekarang, sa_type=TIPE_WAKTU)
    updated_at: datetime = Field(default_factory=sekarang, sa_type=TIPE_WAKTU)


class JobsInfo(SQLModel, table=True):
    """Informasi tahap/tanggal tarik data yang menyertai respons DataTable."""

    __tablename__ = settings.table_meta
    __table_args__ = {"schema": SCHEMA}

    tahun: int = Field(primary_key=True)
    kodepemda: str = Field(primary_key=True, sa_type=Text)
    tahap_renstra: str | None = Field(default=None, sa_type=Text)
    tahap_rkpd: str | None = Field(default=None, sa_type=Text)
    tgl_tarik_renstra: str | None = Field(default=None, sa_type=Text)
    tgl_tarik_rkpd: str | None = Field(default=None, sa_type=Text)
    records_total: int | None = Field(default=None)
    fetched_at: datetime = Field(default_factory=sekarang, sa_type=TIPE_WAKTU)


class DownloadJob(SQLModel, table=True):
    """Riwayat setiap eksekusi tombol Download di extension."""

    __tablename__ = settings.table_jobs
    __table_args__ = {"schema": SCHEMA}

    id: int | None = _pk_bigserial()
    job_id: UUID = Field(default_factory=uuid4, unique=True, index=True)

    # Enum disimpan sebagai varchar supaya nilai baru tidak butuh migrasi tipe.
    jenis_data: JenisData = Field(sa_type=String(20), index=True)
    tahun: int = Field(index=True)
    kodepemda: str = Field(sa_type=Text)
    kodeskpd: str | None = Field(default=None, sa_type=Text)
    perangkat_daerah: str | None = Field(default=None, sa_type=Text)

    mode: ModeSimpan = Field(default=ModeSimpan.replace, sa_type=String(20))
    status: StatusJob = Field(default=StatusJob.berjalan, sa_type=String(20), index=True)
    lengkap: bool = Field(default=False)

    total_baris_server: int | None = Field(default=None)
    jumlah_baris_diterima: int = Field(default=0)
    jumlah_baris_tersimpan: int = Field(default=0)
    jumlah_baris_dihapus: int = Field(default=0)

    sumber_url: str | None = Field(default=None, sa_type=Text)
    catatan: str | None = Field(default=None, sa_type=Text)

    dimulai_pada: datetime = Field(default_factory=sekarang, sa_type=TIPE_WAKTU)
    diperbarui_pada: datetime = Field(default_factory=sekarang, sa_type=TIPE_WAKTU)
    selesai_pada: datetime | None = Field(default=None, sa_type=TIPE_WAKTU)


# Parameter yang dikirim ke `f=tarik_realisasi_keuangan`, urut sesuai form SIPD.
PARAMETER_REALISASI: tuple[str, ...] = (
    "kodesubkegiatan",
    "kodekegiatan",
    "kodeprogram",
    "kodeskpd",
    "tahun",
)

# Kunci unik tabel hasil: parameter + kodepemda.
KUNCI_REALISASI: tuple[str, ...] = (
    "tahun",
    "kodepemda",
    "kodeskpd",
    "kodeprogram",
    "kodekegiatan",
    "kodesubkegiatan",
)

TABEL_PER_JENIS: dict[JenisData, type[BarisDalevBase]] = {
    JenisData.program: RealisasiProgram,
    JenisData.subkegiatan: RealisasiSubkegiatan,
}

# Kolom kunci ON CONFLICT per jenis data.
KUNCI_PER_JENIS: dict[JenisData, tuple[str, ...]] = {
    JenisData.program: (
        "tahun",
        "kodepemda",
        "kodeskpd",
        "kodebidang",
        "kodeprogram",
        "idoutcome",
        "kodeindikator_program",
    ),
    JenisData.subkegiatan: (
        "tahun",
        "kodepemda",
        "kodeskpd",
        "kodesubkegiatan",
        "kodesubkegiatan_indikator",
    ),
}


def model_baris(jenis: JenisData) -> type[BarisDalevBase]:
    return TABEL_PER_JENIS[JenisData(jenis)]


def kunci_baris(jenis: JenisData) -> tuple[str, ...]:
    return KUNCI_PER_JENIS[JenisData(jenis)]
