# REST API SIPD DALEV

Menyimpan hasil tombol **Download Program** dan **Download Subkegiatan** dari
extension Chrome ke PostgreSQL.

Tumpukan: FastAPI, SQLModel/SQLAlchemy 2, psycopg3, pydantic-settings.
Seluruh konfigurasi ada di [.env](.env) (contoh: [.env.example](.env.example)).

## Menjalankan

```bash
cd rest_api
./run.sh                 # membuat .venv otomatis pada pemakaian pertama
./run.sh --reload        # mode pengembangan
```

Dokumentasi interaktif: `http://<host>:<port>/docs`.
Cek kesehatan + koneksi database: `GET /health`.

Saat start, aplikasi membuat schema, tabel, dan **kolom yang belum ada** pada
tabel yang sudah terbentuk (kolom tambahan selalu nullable). Matikan dengan
`CREATE_TABLES=false` bila skema dikelola manual.

## Tabel

| Tabel (bawaan)                | Isi                                                        |
| ----------------------------- | ---------------------------------------------------------- |
| `dalev_realisasi_program`     | Baris tabel realisasi kinerja program (bidang/program/outcome) |
| `dalev_realisasi_subkegiatan` | Baris tabel realisasi subkegiatan (subkegiatan/output)      |
| `dalev_jobs_info`             | Tahap & tanggal tarik data (`jobs_info` dari respons SIPD)  |
| `dalev_download_jobs`         | Riwayat tiap eksekusi tombol Download                       |

Nama kolom mengikuti field JSON SIPD apa adanya (`kodeprogram`, `uraiprogram`,
`rkpd_real_tw1_keu`, ...) sehingga cocok dengan skema project `SIPD_DALEV`.
Kolom tambahan di luar itu:

- `row_type` — tingkat baris hasil terjemahan `xstyle`/`DT_RowClass`
  (`bidang`, `program`, `outcome`, `subkegiatan`, `output`);
- `id_sipd` — field `id` dari respons SIPD;
- `nomor_urut` — field `no` (nomor baris DataTable);
- `job_id`, `fetched_at`, `updated_at` — jejak unduhan;
- `raw` — baris JSON asli, hanya terisi bila `STORE_RAW=true`.

### Kunci unik (idempotensi)

Unduhan berulang **memperbarui** baris yang sama, tidak menduplikasi:

- program: `tahun, kodepemda, kodeskpd, kodebidang, kodeprogram, idoutcome, kodeindikator_program`
- subkegiatan: `tahun, kodepemda, kodeskpd, kodesubkegiatan, kodesubkegiatan_indikator`

Kode tingkat bawah yang NULL pada baris induk disimpan sebagai string kosong
agar `ON CONFLICT` tetap bekerja.

### Mode simpan

- `replace` (bawaan) — setelah job selesai **dan** unduhan dinyatakan lengkap,
  baris pada cakupan yang sama (tahun + kodepemda, ditambah kodeskpd bila
  unduhan difilter per OPD) dari unduhan sebelumnya dihapus. Unduhan yang
  dibatalkan atau gagal tidak menghapus apa pun.
- `upsert` — hanya menambah/memperbarui.

Cakupan penghapusan diambil dari `tahun`/`kodepemda` pada baris yang benar-benar
tertulis, bukan dari parameter yang dikirim extension.

## Endpoint

Semua endpoint berada di bawah `/api/v1` dan memakai header `X-API-Key` bila
`API_KEY` di `.env` tidak kosong.

| Metode | Jalur                    | Kegunaan                                        |
| ------ | ------------------------ | ----------------------------------------------- |
| GET    | `/config`                | Nilai bawaan server (tahun, kode pemda, tabel)  |
| POST   | `/jobs`                  | Mulai job unduhan                               |
| POST   | `/jobs/{job_id}/rows`    | Kirim satu halaman DataTable                    |
| POST   | `/jobs/{job_id}/finish`  | Tutup job (+ `jobs_info`), jalankan pembersihan  |
| GET    | `/jobs`                  | Riwayat job                                     |
| GET    | `/jobs/{job_id}`         | Detail satu job                                 |
| POST   | `/ingest`                | Unggah satu file JSON hasil unduhan sekaligus   |
| GET    | `/data/{jenis}`          | Baca baris (filter tahun/pemda/skpd/kode/row_type) |
| GET    | `/statistik/{jenis}`     | Jumlah baris per `row_type` dan waktu pembaruan  |

`{jenis}` = `program` atau `subkegiatan`.

### Unggah bertahap (dipakai extension)

```bash
JOB=$(curl -s -X POST localhost:8000/api/v1/jobs -H 'content-type: application/json' \
  -d '{"jenis_data":"program","tahun":2026,"kodepemda":"3376","kodeskpd":""}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["job_id"])')

curl -X POST localhost:8000/api/v1/jobs/$JOB/rows \
  -H 'content-type: application/json' -d '{"data":[ ... 100 baris ... ]}'

curl -X POST localhost:8000/api/v1/jobs/$JOB/finish \
  -H 'content-type: application/json' -d '{"lengkap":true,"status":"selesai"}'
```

### Unggah file JSON lama

File hasil tombol download versi sebelumnya bisa dikirim langsung karena
bentuknya sama dengan `POST /ingest`:

```bash
python3 - <<'EOF'
import json, urllib.request
isi = json.load(open("program_3376_2026_20260729_162100.json"))
isi["jenis_data"] = "program"          # sudah ada di file versi baru
req = urllib.request.Request(
    "http://localhost:8000/api/v1/ingest",
    data=json.dumps(isi).encode(),
    headers={"content-type": "application/json"},
)
print(json.loads(urllib.request.urlopen(req).read()))
EOF
```

## Catatan

- `.env` berisi kredensial database dan ikut terlacak git pada repo ini; ganti
  password bila repo dibagikan.
- Nilai angka SIPD datang dalam dua format sekaligus (mentah `107946600.00` dan
  gaya Indonesia `1.100,0`); keduanya diubah ke `numeric`. Adanya koma dipakai
  sebagai penanda format Indonesia.
- Boolean SIPD (`"t"`/`"f"`) diubah ke `boolean`, kolom `lokasi`/`tag`/`valid`/
  `rakortek_tahun`/`pilihan_input` disimpan sebagai `jsonb`.
