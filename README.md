# SIPD DALEV — Extension Chrome + REST API

Menarik seluruh data realisasi **Program** dan **Subkegiatan** dari SIPD DALEV
lalu menyimpannya ke PostgreSQL.

```
chrome_extension/   tombol Download di dashboard DALEV -> kirim ke REST API
rest_api/           FastAPI + SQLModel + psycopg3 -> PostgreSQL
```

## 1. Jalankan REST API

```bash
cd rest_api
cp .env.example .env      # sesuaikan koneksi database bila perlu
./run.sh
```

Rinciannya (tabel, endpoint, kunci unik, mode simpan) ada di
[rest_api/README.md](rest_api/README.md).

## 2. Pasang extension

1. Buka `chrome://extensions`, aktifkan **Developer mode**.
2. **Load unpacked** -> pilih folder [chrome_extension/](chrome_extension/).
3. Buka halaman **Opsi** extension, isi:
   - **Alamat API** — mis. `http://localhost:8000` atau `http://192.168.50.75:8000`
   - **API Key** — kosongkan bila `API_KEY` di `.env` kosong
4. Klik **Uji Koneksi** sampai muncul status `ok`.

Alamat selain `localhost`, `127.0.0.1`, dan `192.168.50.75` akan meminta izin
tambahan saat disimpan; setujui permintaan izin dari Chrome.

## 3. Pakai

Buka dashboard DALEV (`?m=daerah_dalev_dashboard`). Tiga tombol muncul di kartu
Informasi Dashboard: **Download Program**, **Download Subkegiatan**, dan
**Tarik Realisasi Keuangan**.

### Download Program / Subkegiatan

Dialog menyediakan dua tujuan yang bisa dikombinasikan:

- **Simpan ke database lewat REST API** (aktif secara bawaan) — tiap halaman
  (100 baris) langsung dikirim ke API, jadi progres terlihat dan data tidak
  menumpuk di memori browser;
- **Unduh juga sebagai file JSON** — cadangan berisi seluruh baris.

Filter **Perangkat Daerah** di dashboard diikuti: bila satu OPD dipilih, hanya
data OPD tersebut yang ditarik dan hanya cakupan itu yang diperbarui di
database.

Unduhan yang dibatalkan atau gagal tidak menghapus data lama; job dicatat di
tabel `dalev_download_jobs` dengan status `dibatalkan`/`gagal`.

### Tarik Realisasi Keuangan

Menarik detail realisasi keuangan **per indikator output subkegiatan**
(`POST ?m=daerah_dalev_realisasi_subkegiatan&f=load_realisasi`). Daftar
indikatornya dibaca dari database (`dalev_realisasi_subkegiatan` dengan
`row_type='output'`), jadi **jalankan Download Subkegiatan lebih dulu**.

- Centang **Hanya indikator yang belum berhasil ditarik** (bawaan) membuat
  penarikan yang terputus bisa dilanjutkan tanpa mengulang dari awal.
- Jumlahnya besar (mis. 2.844 indikator untuk Kota Tegal 2026) dan jedanya
  250 ms per permintaan, jadi sekali jalan bisa belasan menit. Dialog boleh
  dibatalkan kapan saja; hasil yang sudah masuk tetap tersimpan.
- Bila 5 permintaan gagal berturut-turut (biasanya sesi SIPD habis),
  penarikan berhenti sendiri dengan keterangan penyebabnya.

Segmen `sess` pada URL berbeda antar halaman SIPD. Kalau muncul
"Sesi tidak valid", muat ulang halaman, atau buka halaman **Realisasi
Subkegiatan** (`?m=daerah_dalev_realisasi_subkegiatan`) — tombol yang sama
juga dipasang di sana — lalu ulangi.

## Alur teknis

```
sipd.js (content script)
  |  chrome.runtime.sendMessage
background.js (service worker)      <- perlu karena halaman SIPD HTTPS
  |  fetch                             tidak boleh memanggil API HTTP langsung
REST API  POST /api/v1/jobs
          POST /api/v1/jobs/{id}/rows      (per halaman DataTable)
          POST /api/v1/jobs/{id}/finish    (+ jobs_info, pembersihan data lama)

Tarik Realisasi Keuangan:
REST API  GET  /api/v1/realisasi-keuangan/parameter   (dari baris row_type=output)
SIPD      POST ?m=daerah_dalev_realisasi_subkegiatan&f=load_realisasi   (per indikator)
REST API  POST /api/v1/jobs/{id}/realisasi            (batch 25 hasil)
```
