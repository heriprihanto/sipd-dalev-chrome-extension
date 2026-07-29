/**
 * SIPD DALEV - Download Subkegiatan
 *
 * Menambahkan tombol "Download Subkegiatan" pada halaman dashboard DALEV
 * (?m=daerah_dalev_dashboard). Tombol menarik SELURUH baris DataTable
 * daerah_dalev_realisasi_subkegiatan (looping per halaman sampai habis)
 * lalu menyimpannya sebagai satu file JSON.
 */

const PAKET_DASHBOARD = "daerah_dalev_dashboard";
const PAKET_SUBKEGIATAN = "daerah_dalev_realisasi_subkegiatan";

// Jumlah baris per request. DataTable di halaman aslinya memakai 50;
// 100 lebih hemat request tapi tetap aman untuk server.
const UKURAN_HALAMAN = 100;

// Jeda antar request supaya tidak membebani server SIPD.
const JEDA_MS = 500;

// Kolom persis seperti yang dikirim DataTable halaman subkegiatan.
// Urutan menentukan indeks columns[i] pada payload, jadi jangan diacak.
const KOLOM_SUBKEGIATAN = [
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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
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

function payloadSubkegiatan({ draw, start, kodepemda, kodeskpd }) {
  const p = new URLSearchParams();
  p.set("draw", String(draw));

  KOLOM_SUBKEGIATAN.forEach((kolom, i) => {
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
  p.set("kodeprogram", "");
  p.set("kodekegiatan", "");
  p.set("tematik", "");
  p.set("spm", "Semua");
  p.set("jenis", "Semua");
  p.set("misi_astacita", "");
  p.set("bidang_prioritas", "");
  p.set("program_prioritas", "");
  p.set("kegiatan_prioritas", "");
  p.set("jenis_astacita", "semua");
  p.set("data-valid", "Semua");
  p.set("program_prioritas_nasional", "");
  p.set("realisasi_gap_sumber", "semua");
  p.set("realisasi_gap_tw", "semua");

  return p.toString();
}

async function ambilHalamanSubkegiatan(konfig, opsi) {
  const url = `${konfig.baseUrl}/?m=${PAKET_SUBKEGIATAN}&f=table_subkegiatan`;

  const res = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: {
      accept: "application/json, text/javascript, */*; q=0.01",
      "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
      "x-requested-with": "XMLHttpRequest",
    },
    body: payloadSubkegiatan(opsi),
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
 * `onProgress` dipanggil tiap halaman selesai, `batal()` dicek sebelum
 * request berikutnya supaya tombol Batal terasa responsif.
 */
async function ambilSemuaSubkegiatan(konfig, kodeskpd, onProgress, batal) {
  const baris = [];
  let start = 0;
  let draw = 1;
  let total = null;

  while (true) {
    const hasil = await ambilHalamanSubkegiatan(konfig, {
      draw: draw++,
      start,
      kodepemda: konfig.kodepemda,
      kodeskpd,
    });

    const data = Array.isArray(hasil.data) ? hasil.data : [];
    if (total === null) {
      total = Number(hasil.recordsFiltered ?? hasil.recordsTotal ?? data.length);
    }

    baris.push(...data);
    onProgress(baris.length, total);

    if (data.length === 0 || baris.length >= total) break;
    if (batal()) break;

    start += UKURAN_HALAMAN;
    await sleep(JEDA_MS);
  }

  return { baris, total: total ?? baris.length };
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

function bukaModalUnduh(konfig) {
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
      <i class="fa fa-download"></i> Download Subkegiatan
    </h4>
    <table style="width:100%;font-size:13px;margin-bottom:14px;">
      <tr><td style="width:38%;color:#666;padding:2px 0;">Tahun</td><td>: ${konfig.tahun}</td></tr>
      <tr><td style="color:#666;padding:2px 0;">Kode Pemda</td><td>: ${konfig.kodepemda}</td></tr>
      <tr><td style="color:#666;padding:2px 0;vertical-align:top;">Perangkat Daerah</td><td>: ${labelOpd}</td></tr>
    </table>
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
    sedangJalan = true;
    dibatalkan = false;
    btnMulai.disabled = true;
    btnTutup.textContent = "Batal";
    status.textContent = "Mengambil data...";

    try {
      const { baris, total } = await ambilSemuaSubkegiatan(
        konfig,
        kodeskpd,
        (terambil, jumlah) => {
          const persen = jumlah ? Math.round((terambil / jumlah) * 100) : 100;
          bar.style.width = `${Math.min(persen, 100)}%`;
          status.textContent = `Mengambil data... ${terambil} dari ${jumlah} baris (${persen}%)`;
        },
        () => dibatalkan,
      );

      const batalDipakai = dibatalkan;
      if (batalDipakai) {
        status.innerHTML = `<span style="color:#a94442;">Dibatalkan.</span> ${baris.length} baris yang sempat terambil tetap diunduh.`;
      }

      const namaFile = `subkegiatan_${konfig.kodepemda}_${konfig.tahun}${
        kodeskpd ? `_${kodeskpd}` : ""
      }_${stempelWaktu()}.json`;

      unduhJson(
        {
          tahun: konfig.tahun,
          kodepemda: konfig.kodepemda,
          kodeskpd: kodeskpd || null,
          perangkat_daerah: labelOpd,
          diambil_pada: new Date().toISOString(),
          jumlah_baris: baris.length,
          total_baris_server: total,
          lengkap: !batalDipakai && baris.length >= total,
          data: baris,
        },
        namaFile,
      );

      if (!batalDipakai) {
        bar.style.width = "100%";
        status.innerHTML = `<span style="color:#3c763d;">Selesai.</span> ${baris.length} baris tersimpan ke <b>${namaFile}</b>.`;
      }
    } catch (err) {
      console.error("[Download Subkegiatan]", err);
      bar.style.background = "#d9534f";
      status.innerHTML = `<span style="color:#a94442;">Gagal:</span> ${err.message}`;
    } finally {
      sedangJalan = false;
      dibatalkan = false;
      btnMulai.disabled = false;
      btnTutup.textContent = "Tutup";
    }
  });
}

/* ------------------------------------------------------------------ *
 * Penempatan tombol
 * ------------------------------------------------------------------ */

function buatTombol(konfig) {
  const tombol = document.createElement("button");
  tombol.type = "button";
  tombol.id = "btn-download-subkegiatan";
  tombol.className = "btn btn-primary btn-sm";
  tombol.title = "Unduh seluruh data realisasi subkegiatan sebagai JSON";
  tombol.innerHTML = '<i class="fa fa-download"></i> Download Subkegiatan';
  tombol.addEventListener("click", () => bukaModalUnduh(konfig));
  return tombol;
}

function pasangTombol(konfig) {
  if (document.getElementById("btn-download-subkegiatan")) return true;

  const tombol = buatTombol(konfig);

  // Prioritas 1: sebelah tombol "Perbarui Data" di kartu Informasi Dashboard.
  const headerInfo = document.querySelector(".dashboard-info-header");
  if (headerInfo) {
    tombol.style.marginRight = "6px";
    const btnRefresh = headerInfo.querySelector(".dashboard-btn-refresh");
    if (btnRefresh) {
      btnRefresh.parentNode.insertBefore(tombol, btnRefresh);
    } else {
      headerInfo.appendChild(tombol);
    }
    return true;
  }

  // Prioritas 2: baris tombol Terapkan/Reset pada kartu filter.
  const aksiFilter = document.querySelector(".dashboard-filter-action-btns");
  if (aksiFilter) {
    aksiFilter.appendChild(tombol);
    return true;
  }

  return false;
}

/** Cadangan kalau tata letak dashboard berubah: tombol mengambang. */
function pasangTombolMengambang(konfig) {
  if (document.getElementById("btn-download-subkegiatan")) return;
  const tombol = buatTombol(konfig);
  tombol.style.cssText = `
    position: fixed; right: 20px; bottom: 20px; z-index: 19999;
    box-shadow: 0 2px 10px rgba(0,0,0,.3);
  `;
  document.body.appendChild(tombol);
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
      "[Download Subkegiatan] sess tidak ditemukan di URL, tombol tidak dipasang.",
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
