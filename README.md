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

Buka dashboard DALEV (`?m=daerah_dalev_dashboard`). Dua tombol muncul di kartu
Informasi Dashboard: **Download Program** dan **Download Subkegiatan**.

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

## Alur teknis

```
sipd.js (content script)
  |  chrome.runtime.sendMessage
background.js (service worker)      <- perlu karena halaman SIPD HTTPS
  |  fetch                             tidak boleh memanggil API HTTP langsung
REST API  POST /api/v1/jobs
          POST /api/v1/jobs/{id}/rows      (per halaman)
          POST /api/v1/jobs/{id}/finish    (+ jobs_info, pembersihan data lama)
```
