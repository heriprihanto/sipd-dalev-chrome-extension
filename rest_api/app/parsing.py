"""Normalisasi satu baris JSON DataTable SIPD DALEV menjadi baris tabel.

Ciri respons SIPD yang perlu ditangani:

* dua format angka dalam satu respons — kolom keuangan mentah
  ("229580744248.00000000") dan kolom kinerja gaya Indonesia ("1.100,0");
* boolean gaya Postgres ("t"/"f");
* kolom JSON yang kadang dikirim sebagai objek (`valid`, `rakortek_tahun`)
  dan kadang sebagai string berisi JSON (`lokasi`, `tag`, `pilihan_input`);
* baris induk (bidang/program/subkegiatan) yang kode tingkat bawahnya NULL,
  padahal kolom kunci tidak boleh NULL.
"""

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import JenisData, kunci_baris, model_baris

# Field respons yang tidak disimpan sebagai kolom sendiri.
_ABAIKAN = {"no", "id", "aksi", "DT_RowClass", "DT_RowAttr"}

_KOLOM_JSON = {"lokasi", "tag", "valid", "rakortek_tahun", "pilihan_input"}

# Peta kolom -> jenis nilai per tabel; dihitung sekali lalu di-cache.
_PETA_KOLOM: dict[str, dict[str, str]] = {}

# DT_RowClass "monev-row-bidang" -> "bidang".
_PREFIKS_ROW_CLASS = "monev-row-"

# Cadangan kalau DT_RowClass tidak dikirim. Tingkat 1-3 muncul di tabel
# program, 6-7 di tabel subkegiatan.
_ROW_TYPE_PER_XSTYLE = {
    "1": "bidang",
    "2": "program",
    "3": "outcome",
    "4": "kegiatan",
    "5": "output",
    "6": "subkegiatan",
    "7": "indikator",
}

_ANGKA_VALID = re.compile(r"^-?\d+(\.\d+)?$")


def peta_kolom(jenis: JenisData) -> dict[str, str]:
    """Kolom tabel beserta jenis nilainya: json/bool/int/angka/teks."""
    jenis = JenisData(jenis)
    if jenis.value in _PETA_KOLOM:
        return _PETA_KOLOM[jenis.value]

    peta: dict[str, str] = {}
    for kolom in model_baris(jenis).__table__.columns:
        if kolom.name in _KOLOM_JSON:
            peta[kolom.name] = "json"
            continue
        try:
            tipe = kolom.type.python_type
        except NotImplementedError:  # pragma: no cover - tipe khusus
            peta[kolom.name] = "teks"
            continue
        if tipe is bool:
            peta[kolom.name] = "bool"
        elif tipe is int:
            peta[kolom.name] = "int"
        elif tipe is Decimal:
            peta[kolom.name] = "angka"
        else:
            peta[kolom.name] = "teks"

    _PETA_KOLOM[jenis.value] = peta
    return peta


def teks(nilai: Any) -> str | None:
    """String yang sudah dirapikan, atau None bila kosong."""
    if nilai is None:
        return None
    hasil = str(nilai).strip()
    return hasil or None


def ke_angka(nilai: Any) -> Decimal | None:
    """Ubah nilai angka SIPD menjadi Decimal.

    Adanya koma dipakai sebagai penanda format Indonesia ("1.100,0" -> 1100.0);
    tanpa koma nilai dianggap format mentah ("107946600.00").
    """
    if nilai is None or isinstance(nilai, bool):
        return None
    if isinstance(nilai, (int, float, Decimal)):
        return Decimal(str(nilai))

    hasil = str(nilai).strip().replace(" ", "").replace("%", "")
    if not hasil or hasil in {"-", "null", "NULL"}:
        return None

    if "," in hasil:
        hasil = hasil.replace(".", "").replace(",", ".")
    if not _ANGKA_VALID.match(hasil):
        return None

    try:
        return Decimal(hasil)
    except InvalidOperation:
        return None


def ke_int(nilai: Any) -> int | None:
    angka = ke_angka(nilai)
    return int(angka) if angka is not None else None


def ke_bool(nilai: Any) -> bool | None:
    """SIPD mengirim boolean gaya Postgres ('t'/'f')."""
    if nilai is None:
        return None
    if isinstance(nilai, bool):
        return nilai
    hasil = str(nilai).strip().lower()
    if hasil in {"t", "true", "1", "y", "ya"}:
        return True
    if hasil in {"f", "false", "0", "n", "tidak"}:
        return False
    return None


def ke_json(nilai: Any) -> Any | None:
    """Nilai siap disimpan ke kolom jsonb."""
    if nilai is None or nilai == "":
        return None
    if isinstance(nilai, str):
        try:
            nilai = json.loads(nilai)
        except json.JSONDecodeError:
            return [nilai]
    if isinstance(nilai, (list, dict)) and not nilai:
        return None
    return nilai


def row_type(baris: dict[str, Any]) -> str | None:
    """Tingkat baris pada hirarki tabel."""
    kelas = teks(baris.get("DT_RowClass"))
    if kelas:
        for bagian in kelas.split():
            if bagian.startswith(_PREFIKS_ROW_CLASS):
                return bagian[len(_PREFIKS_ROW_CLASS) :]
    xstyle = teks(baris.get("xstyle"))
    return _ROW_TYPE_PER_XSTYLE.get(xstyle or "", "lainnya")


def normalisasi_baris(
    baris: dict[str, Any],
    *,
    jenis: JenisData,
    tahun: int,
    kodepemda: str,
    simpan_raw: bool = False,
) -> dict[str, Any]:
    """Ubah satu record JSON menjadi dict kolom -> nilai siap-insert."""
    peta = peta_kolom(jenis)
    ubah = {"json": ke_json, "bool": ke_bool, "int": ke_int, "angka": ke_angka}
    hasil: dict[str, Any] = {}

    for nama, nilai in baris.items():
        if nama in _ABAIKAN or nama not in peta:
            continue
        hasil[nama] = ubah.get(peta[nama], teks)(nilai)

    hasil["row_type"] = row_type(baris)
    hasil["id_sipd"] = teks(baris.get("id"))
    hasil["nomor_urut"] = ke_int(baris.get("no"))
    hasil["tahun"] = ke_int(baris.get("tahun")) or tahun
    hasil["kodepemda"] = teks(baris.get("kodepemda")) or kodepemda
    if simpan_raw:
        hasil["raw"] = baris

    # Kolom kunci tidak boleh NULL agar ON CONFLICT tetap bekerja.
    for nama in kunci_baris(jenis):
        if nama == "tahun":
            continue
        if not hasil.get(nama):
            hasil[nama] = ""

    return hasil


def buang_duplikat(
    baris: list[dict[str, Any]], jenis: JenisData
) -> list[dict[str, Any]]:
    """Buang duplikat kunci dalam satu batch (baris terakhir yang menang).

    Postgres menolak `ON CONFLICT DO UPDATE` bila satu perintah INSERT
    menyentuh baris tujuan yang sama dua kali.
    """
    kunci = kunci_baris(jenis)
    unik: dict[tuple, dict[str, Any]] = {}
    for satu in baris:
        unik[tuple(satu.get(k) for k in kunci)] = satu
    return list(unik.values())
