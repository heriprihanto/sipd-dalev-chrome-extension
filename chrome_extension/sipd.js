/**
 * SIPD DALEV - Download Program & Subkegiatan
 *
 * Menambahkan tombol "Download Program" dan "Download Subkegiatan" pada
 * halaman dashboard DALEV (?m=daerah_dalev_dashboard). Tombol menarik SELURUH
 * baris DataTable terkait (looping per halaman sampai habis), lalu tiap
 * halaman langsung dikirim ke REST API untuk disimpan ke PostgreSQL. File JSON
 * tetap bisa diunduh sebagai cadangan lewat pilihan di dialog.
 *
 * Permintaan ke API dijalankan service worker (background.js), bukan dari sini,
 * karena halaman SIPD memakai HTTPS sedangkan API biasanya HTTP di jaringan
 * lokal.
 */

const PAKET_DASHBOARD = "daerah_dalev_dashboard";

// Jumlah baris per request. DataTable aslinya memakai 50-100;
// 100 lebih hemat request tapi tetap aman untuk server.
const UKURAN_HALAMAN = 100;

// Jeda antar request supaya tidak membebani server SIPD.
const JEDA_MS = 500;

// Kolom persis seperti yang dikirim DataTable halaman program/subkegiatan.
// Kedua tabel memakai susunan kolom yang sama. Urutan menentukan indeks
// columns[i] pada payload, jadi jangan diacak.
const KOLOM_DATATABLE = [
  { data: "no", name: "", orderable: false },
  { data: "title", name: "title" },
  { data: "indikator", name: "indikator" },
  { data: "satuan", name: "satuan" },
  { data: "renstra_target_kin", name: "" },
  { data: "renstra_target_keu", name: "" },
  { data: "rkpd_target_kin", name: "" },
  { data: "rkpd_target_keu", name: "" },
  { data: "rkpd_real_tw1_kin", name: "" },
  { data: "rkpd_real_tw1_keu", name: "" },
  { data: "rkpd_real_tw2_kin", name: "" },
  { data: "rkpd_real_tw2_keu", name: "" },
  { data: "rkpd_real_tw3_kin", name: "" },
  { data: "rkpd_real_tw3_keu", name: "" },
  { data: "rkpd_real_tw4_kin", name: "" },
  { data: "rkpd_real_tw4_keu", name: "" },
  { data: "aksi", name: "aksi", orderable: false },
];

/**
 * Dua tabel memakai endpoint dan filter tambahan yang berbeda. `filter`
 * ditulis urut sesuai payload asli halaman; kodepemda dan kodeskpd disisipkan
 * lebih dulu oleh pembangun payload karena posisinya selalu di depan.
 */
const DATASET = {
  program: {
    label: "Program",
    paket: "daerah_dalev_realisasi_kinerja_program",
    fungsi: "table_program",
    filter: {
      kodeprogram: "",
      tematik: "",
      spm: "Semua",
      jenis: "Semua",
      "data-valid": "Semua",
      program_prioritas_nasional: "",
    },
  },
  subkegiatan: {
    label: "Subkegiatan",
    paket: "daerah_dalev_realisasi_subkegiatan",
    fungsi: "table_subkegiatan",
    filter: {
      kodeprogram: "",
      kodekegiatan: "",
      tematik: "",
      spm: "Semua",
      jenis: "Semua",
      misi_astacita: "",
      bidang_prioritas: "",
      program_prioritas: "",
      kegiatan_prioritas: "",
      jenis_astacita: "semua",
      "data-valid": "Semua",
      program_prioritas_nasional: "",
      realisasi_gap_sumber: "semua",
      realisasi_gap_tw: "semua",
    },
  },
};

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/* ------------------------------------------------------------------ *
 * REST API (lewat service worker)
 * ------------------------------------------------------------------ */

async function apiJson(jalur, metode, body) {
  const balasan = await chrome.runtime.sendMessage({
    tipe: "api",
    jalur,
    metode,
    body,
  });
  if (!balasan) {
    throw new Error(
      "Service worker extension tidak merespons. Muat ulang extension lalu coba lagi.",
    );
  }
  if (!balasan.ok) throw new Error(balasan.pesan);
  return balasan.data;
}

/**
 * Halaman menyimpan sess/tahun/kodepemda di window.SIPD_QOL, tapi content
 * script berjalan di isolated world sehingga tidak bisa membaca variabel itu
 * langsung. Isinya dibaca ulang dari teks <script> di halaman, dengan
 * cadangan dari URL dan elemen filter kalau formatnya berubah.
 */
function konfigHalaman() {
  const segmen = location.pathname.split("/").filter(Boolean);
  const sess = segmen[1] || "";

  let tahun = "";
  let kodepemda = "";

  const teksScript = Array.from(document.scripts)
    .map((s) => s.textContent || "")
    .join("\n");
  const blok = teksScript.match(/SIPD_QOL\s*=\s*\{([\s\S]*?)\}/);
  if (blok) {
    const ambil = (kunci) => {
      const cocok = blok[1].match(new RegExp(`${kunci}\\s*:\\s*"([^"]*)"`));
      return cocok ? cocok[1] : "";
    };
    tahun = ambil("tahun");
    kodepemda = ambil("kodepemda");
  }

  if (!kodepemda) {
    kodepemda = document.querySelector("#filter-pemda")?.value || "";
  }
  if (!tahun) {
    tahun = String(new Date().getFullYear());
  }

  return {
    sess,
    tahun,
    kodepemda,
    baseUrl: `${location.origin}/dalev/${sess}`,
  };
}

/** Perangkat Daerah yang sedang dipilih di filter dashboard ("" = semua OPD). */
function kodeSkpdTerpilih() {
  return document.querySelector("#fr-kodeskpd-dashboard-rs")?.value || "";
}

function payloadDatatable(dataset, { draw, start, kodepemda, kodeskpd }) {
  const p = new URLSearchParams();
  p.set("draw", String(draw));

  KOLOM_DATATABLE.forEach((kolom, i) => {
    p.set(`columns[${i}][data]`, kolom.data);
    p.set(`columns[${i}][name]`, kolom.name);
    p.set(`columns[${i}][searchable]`, "false");
    p.set(
      `columns[${i}][orderable]`,
      kolom.orderable === false ? "false" : "true",
    );
    p.set(`columns[${i}][search][value]`, "");
    p.set(`columns[${i}][search][regex]`, "false");
  });

  p.set("start", String(start));
  p.set("length", String(UKURAN_HALAMAN));
  p.set("search[value]", "");
  p.set("search[regex]", "false");

  p.set("kodepemda", kodepemda);
  p.set("kodeskpd", kodeskpd);
  for (const [nama, nilai] of Object.entries(dataset.filter)) {
    p.set(nama, nilai);
  }

  return p.toString();
}

async function ambilSatuHalaman(konfig, dataset, opsi) {
  const url = `${konfig.baseUrl}/?m=${dataset.paket}&f=${dataset.fungsi}`;

  const res = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: {
      accept: "application/json, text/javascript, */*; q=0.01",
      "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
      "x-requested-with": "XMLHttpRequest",
    },
    body: payloadDatatable(dataset, opsi),
  });

  if (!res.ok) {
    throw new Error(
      `Server menolak permintaan (HTTP ${res.status} ${res.statusText}).`,
    );
  }

  // Kalau sesi habis, SIPD membalas halaman login (HTML) dengan status 200.
  const teks = await res.text();
  try {
    return JSON.parse(teks);
  } catch {
    throw new Error(
      "Respons bukan JSON. Sesi kemungkinan sudah habis, silakan muat ulang halaman lalu login kembali.",
    );
  }
}

/**
 * Menarik semua baris dengan looping start += UKURAN_HALAMAN.
 *
 * `onHalaman` dipanggil (dan ditunggu) tiap halaman selesai diambil sehingga
 * penyimpanan ke database berjalan bertahap; `onProgress` memperbarui tampilan;
 * `batal()` dicek sebelum request berikutnya supaya tombol Batal responsif.
 * `simpanSemua` bisa dimatikan agar baris tidak ditumpuk di memori ketika file
 * JSON tidak diminta.
 */
async function ambilSemuaBaris(
  konfig,
  dataset,
  kodeskpd,
  { onProgress, onHalaman, batal, simpanSemua = true },
) {
  const baris = [];
  let start = 0;
  let draw = 1;
  let total = null;
  let terambil = 0;
  let infoTahap = null;

  while (true) {
    const hasil = await ambilSatuHalaman(konfig, dataset, {
      draw: draw++,
      start,
      kodepemda: konfig.kodepemda,
      kodeskpd,
    });

    const data = Array.isArray(hasil.data) ? hasil.data : [];
    if (total === null) {
      total = Number(hasil.recordsFiltered ?? hasil.recordsTotal ?? data.length);
    }
    // Tahap & tanggal tarik data disertakan SIPD di tiap respons.
    if (!infoTahap && hasil.jobs_info) infoTahap = hasil.jobs_info;

    terambil += data.length;
    if (simpanSemua) baris.push(...data);
    if (onHalaman) await onHalaman(data, { total, terambil, infoTahap });
    onProgress(terambil, total);

    if (data.length === 0 || terambil >= total) break;
    if (batal()) break;

    start += UKURAN_HALAMAN;
    await sleep(JEDA_MS);
  }

  return { baris, terambil, total: total ?? terambil, infoTahap };
}

function unduhJson(obj, namaFile) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = namaFile;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function stempelWaktu() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}` +
    `_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
  );
}

/* ------------------------------------------------------------------ *
 * Modal progres
 * ------------------------------------------------------------------ */

function bukaModalUnduh(konfig, kunciDataset) {
  const dataset = DATASET[kunciDataset];
  const kodeskpd = kodeSkpdTerpilih();
  const selectOpd = document.querySelector("#fr-kodeskpd-dashboard-rs");
  const labelOpd = kodeskpd
    ? selectOpd?.selectedOptions?.[0]?.textContent?.trim() || kodeskpd
    : "Semua Perangkat Daerah";

  const backdrop = document.createElement("div");
  backdrop.style.cssText = `
    position: fixed; inset: 0; z-index: 20000;
    background: rgba(0,0,0,.5);
    display: flex; align-items: center; justify-content: center;
  `;

  const kotak = document.createElement("div");
  kotak.style.cssText = `
    background: #fff; border-radius: 8px; padding: 20px 24px;
    width: 460px; max-width: 92vw;
    box-shadow: 0 6px 24px rgba(0,0,0,.3);
  `;
  kotak.innerHTML = `
    <h4 style="margin:0 0 12px;font-weight:600;">
      <i class="fa fa-download"></i> Download ${dataset.label}
    </h4>
    <table style="width:100%;font-size:13px;margin-bottom:14px;">
      <tr><td style="width:38%;color:#666;padding:2px 0;">Tahun</td><td>: ${konfig.tahun}</td></tr>
      <tr><td style="color:#666;padding:2px 0;">Kode Pemda</td><td>: ${konfig.kodepemda}</td></tr>
      <tr><td style="color:#666;padding:2px 0;vertical-align:top;">Perangkat Daerah</td><td>: ${labelOpd}</td></tr>
    </table>
    <div style="font-size:13px;margin-bottom:12px;">
      <label style="display:block;font-weight:400;margin:0 0 4px;">
        <input type="checkbox" id="dsk-ke-db" checked style="margin-right:6px;">
        Simpan ke database lewat REST API
      </label>
      <label style="display:block;font-weight:400;margin:0;">
        <input type="checkbox" id="dsk-ke-file" style="margin-right:6px;">
        Unduh juga sebagai file JSON
      </label>
    </div>
    <div id="dsk-status" style="font-size:13px;margin-bottom:8px;">
      Siap mengunduh. Data diambil bertahap ${UKURAN_HALAMAN} baris per permintaan.
    </div>
    <div style="height:8px;background:#eee;border-radius:4px;overflow:hidden;margin-bottom:16px;">
      <div id="dsk-bar" style="height:100%;width:0%;background:#5cb85c;transition:width .2s;"></div>
    </div>
    <div style="text-align:right;">
      <button type="button" id="dsk-tutup" class="btn btn-default btn-sm">Tutup</button>
      <button type="button" id="dsk-mulai" class="btn btn-success btn-sm">
        <i class="fa fa-download"></i> Mulai Unduh
      </button>
    </div>
  `;

  backdrop.appendChild(kotak);
  document.body.appendChild(backdrop);

  const status = kotak.querySelector("#dsk-status");
  const bar = kotak.querySelector("#dsk-bar");
  const btnTutup = kotak.querySelector("#dsk-tutup");
  const btnMulai = kotak.querySelector("#dsk-mulai");
  const cbKeDb = kotak.querySelector("#dsk-ke-db");
  const cbKeFile = kotak.querySelector("#dsk-ke-file");

  let sedangJalan = false;
  let dibatalkan = false;

  const tutup = () => {
    if (sedangJalan) {
      dibatalkan = true;
      status.textContent = "Membatalkan setelah permintaan berjalan selesai...";
      return;
    }
    backdrop.remove();
  };

  btnTutup.addEventListener("click", tutup);
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) tutup();
  });

  btnMulai.addEventListener("click", async () => {
    if (sedangJalan) return;

    const keDb = cbKeDb.checked;
    const keFile = cbKeFile.checked;
    if (!keDb && !keFile) {
      status.innerHTML =
        '<span style="color:#a94442;">Pilih minimal satu tujuan:</span> database atau file JSON.';
      return;
    }

    sedangJalan = true;
    dibatalkan = false;
    btnMulai.disabled = true;
    cbKeDb.disabled = true;
    cbKeFile.disabled = true;
    btnTutup.textContent = "Batal";
    status.textContent = "Mengambil data...";
    bar.style.background = "#5cb85c";
    bar.style.width = "0%";

    // Job dibuat setelah halaman pertama tiba supaya total baris server ikut
    // tercatat; null berarti belum ada job yang perlu ditutup.
    let job = null;
    let tersimpanDb = 0;

    const tutupJob = async (lengkap, statusJob, catatan, infoTahap) => {
      if (!job) return null;
      const hasil = await apiJson(`/api/v1/jobs/${job.job_id}/finish`, "POST", {
        lengkap,
        status: statusJob,
        catatan: catatan || null,
        jobs_info: infoTahap || null,
      });
      job = null;
      return hasil;
    };

    try {
      const { baris, terambil, total, infoTahap } = await ambilSemuaBaris(
        konfig,
        dataset,
        kodeskpd,
        {
          simpanSemua: keFile,
          batal: () => dibatalkan,
          onProgress: (sudah, jumlah) => {
            const persen = jumlah ? Math.round((sudah / jumlah) * 100) : 100;
            bar.style.width = `${Math.min(persen, 100)}%`;
            const imbuhan = keDb ? ` — ${tersimpanDb} tersimpan di database` : "";
            status.textContent =
              `Mengambil data... ${sudah} dari ${jumlah} baris (${persen}%)` +
              imbuhan;
          },
          onHalaman: async (dataHalaman, info) => {
            if (!keDb || dataHalaman.length === 0) return;

            if (!job) {
              job = await apiJson("/api/v1/jobs", "POST", {
                jenis_data: kunciDataset,
                tahun: Number(konfig.tahun),
                kodepemda: konfig.kodepemda,
                kodeskpd: kodeskpd || "",
                perangkat_daerah: labelOpd,
                total_baris_server: info.total,
                mode: "replace",
                sumber_url: location.href,
              });
            }

            const hasil = await apiJson(
              `/api/v1/jobs/${job.job_id}/rows`,
              "POST",
              { data: dataHalaman },
            );
            tersimpanDb = hasil.total_tersimpan;
          },
        },
      );

      const batalDipakai = dibatalkan;
      const lengkap = !batalDipakai && terambil >= total;

      let ringkasanDb = "";
      if (keDb) {
        const hasilJob = await tutupJob(
          lengkap,
          batalDipakai ? "dibatalkan" : "selesai",
          batalDipakai ? "Dibatalkan pengguna dari dashboard." : null,
          infoTahap,
        );
        if (hasilJob) {
          ringkasanDb =
            ` ${hasilJob.jumlah_baris_tersimpan} baris tersimpan ke database` +
            (hasilJob.jumlah_baris_dihapus
              ? `, ${hasilJob.jumlah_baris_dihapus} baris lama dihapus`
              : "") +
            ".";
        }
      }

      let ringkasanFile = "";
      if (keFile) {
        const namaFile = `${kunciDataset}_${konfig.kodepemda}_${konfig.tahun}${
          kodeskpd ? `_${kodeskpd}` : ""
        }_${stempelWaktu()}.json`;

        unduhJson(
          {
            jenis_data: kunciDataset,
            tahun: konfig.tahun,
            kodepemda: konfig.kodepemda,
            kodeskpd: kodeskpd || null,
            perangkat_daerah: labelOpd,
            diambil_pada: new Date().toISOString(),
            jumlah_baris: baris.length,
            total_baris_server: total,
            lengkap,
            jobs_info: infoTahap || null,
            data: baris,
          },
          namaFile,
        );
        ringkasanFile = ` File <b>${namaFile}</b> diunduh.`;
      }

      if (batalDipakai) {
        status.innerHTML =
          `<span style="color:#a94442;">Dibatalkan</span> pada ${terambil} dari ${total} baris.` +
          `${ringkasanDb}${ringkasanFile}` +
          (keDb
            ? " Data lama tidak dihapus karena unduhan belum lengkap."
            : "");
      } else {
        bar.style.width = "100%";
        status.innerHTML =
          `<span style="color:#3c763d;">Selesai.</span> ${terambil} baris terambil.` +
          `${ringkasanDb}${ringkasanFile}`;
      }
    } catch (err) {
      console.error(`[Download ${dataset.label}]`, err);
      bar.style.background = "#d9534f";
      // Pesan error dipasang sebagai teks, bukan HTML, karena isinya bisa
      // berasal dari respons server.
      status.innerHTML = '<span style="color:#a94442;">Gagal:</span> ';
      status.appendChild(document.createTextNode(err.message));

      // Job yang sudah terbuka ditandai gagal supaya riwayatnya jelas dan
      // baris lama tidak terhapus.
      try {
        await tutupJob(false, "gagal", err.message, null);
      } catch (errTutup) {
        console.error("[Download] gagal menutup job", errTutup);
      }
    } finally {
      sedangJalan = false;
      dibatalkan = false;
      btnMulai.disabled = false;
      cbKeDb.disabled = false;
      cbKeFile.disabled = false;
      btnTutup.textContent = "Tutup";
    }
  });
}

/* ------------------------------------------------------------------ *
 * Penempatan tombol
 * ------------------------------------------------------------------ */

function idTombol(kunciDataset) {
  return `btn-download-${kunciDataset}`;
}

function buatTombol(konfig, kunciDataset) {
  const tombol = document.createElement("button");
  tombol.type = "button";
  tombol.id = idTombol(kunciDataset);
  tombol.className = "btn btn-primary btn-sm";
  tombol.style.marginRight = "6px";
  tombol.title = `Tarik seluruh data realisasi ${DATASET[
    kunciDataset
  ].label.toLowerCase()} lalu simpan ke database (opsional: unduh JSON)`;
  tombol.innerHTML = `<i class="fa fa-download"></i> Download ${DATASET[kunciDataset].label}`;
  tombol.addEventListener("click", () => bukaModalUnduh(konfig, kunciDataset));
  return tombol;
}

/** Mengembalikan wadah tombol pada dashboard, atau null kalau belum ada. */
function wadahTombol() {
  // Prioritas 1: sebelah tombol "Perbarui Data" di kartu Informasi Dashboard.
  const headerInfo = document.querySelector(".dashboard-info-header");
  if (headerInfo) {
    return {
      elemen: headerInfo,
      sebelum: headerInfo.querySelector(".dashboard-btn-refresh"),
    };
  }

  // Prioritas 2: baris tombol Terapkan/Reset pada kartu filter.
  const aksiFilter = document.querySelector(".dashboard-filter-action-btns");
  if (aksiFilter) return { elemen: aksiFilter, sebelum: null };

  return null;
}

function pasangTombol(konfig) {
  const wadah = wadahTombol();
  if (!wadah) return false;

  for (const kunci of Object.keys(DATASET)) {
    if (document.getElementById(idTombol(kunci))) continue;
    const tombol = buatTombol(konfig, kunci);
    if (wadah.sebelum) {
      wadah.sebelum.parentNode.insertBefore(tombol, wadah.sebelum);
    } else {
      wadah.elemen.appendChild(tombol);
    }
  }
  return true;
}

/** Cadangan kalau tata letak dashboard berubah: tombol mengambang. */
function pasangTombolMengambang(konfig) {
  if (document.getElementById("dsk-floating")) return;

  const kotak = document.createElement("div");
  kotak.id = "dsk-floating";
  kotak.style.cssText = `
    position: fixed; right: 20px; bottom: 20px; z-index: 19999;
    display: flex; gap: 6px;
  `;
  for (const kunci of Object.keys(DATASET)) {
    if (document.getElementById(idTombol(kunci))) continue;
    const tombol = buatTombol(konfig, kunci);
    tombol.style.boxShadow = "0 2px 10px rgba(0,0,0,.3)";
    kotak.appendChild(tombol);
  }
  document.body.appendChild(kotak);
}

function halamanDashboardDalev() {
  const paket = new URLSearchParams(location.search).get("m");
  return location.pathname.startsWith("/dalev/") && paket === PAKET_DASHBOARD;
}

function init() {
  if (!halamanDashboardDalev()) return;

  const konfig = konfigHalaman();
  if (!konfig.sess) {
    console.warn(
      "[Download DALEV] sess tidak ditemukan di URL, tombol tidak dipasang.",
    );
    return;
  }

  if (pasangTombol(konfig)) return;

  // Kartu dashboard bisa dirender belakangan; coba ulang sebentar
  // sebelum jatuh ke tombol mengambang.
  let sisa = 20;
  const timer = setInterval(() => {
    if (pasangTombol(konfig)) {
      clearInterval(timer);
    } else if (--sisa <= 0) {
      clearInterval(timer);
      pasangTombolMengambang(konfig);
    }
  }, 500);
}

init();
