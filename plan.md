eksekusi download Program dan Downloaad subkegiatan menyimpan ke database via REST API
buat rest api dengan python, fastapi, sqlalchemy, sqlmodel, psycopg3.
configurasi di file .env

## REALISASI KEUANGAN
Pada Chrome extension, tambahkan Button Tarik Realisasi Keuangan untuk eksekusi 
POST https://sipd.kemendagri.go.id/dalev/533262de43c101e0416a376973112023a7824593/?m=daerah_dalev_realisasi_subkegiatan&f=load_realisasi
Form Data :
tahun
kodeskpd
kodeprogram
kodebidang
kodesubkegiatan
kodekegiatan
idoutcome
idoutput
kodesubkegiatan_indikator

parameter dari loop tabel dalev_realisasi_subkegiatan  where row_type='output'



Revisi Tarik Realisasi Keuangan,
POST https://sipd.kemendagri.go.id/dalev/533262de43c101e0416a376973112023a7824593/?m=daerah_dalev_realisasi_subkegiatan&f=tarik_realisasi_keuangan
Form Data 
kodesubkegiatan
kodekegiatan
kodeprogram
kodeskpd
tahun
