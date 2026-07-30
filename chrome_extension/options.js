/** Halaman Opsi: alamat REST API dan API key. */

const BAWAAN = { apiBaseUrl: "http://localhost:8000", apiKey: "" };

const elBaseUrl = document.getElementById("apiBaseUrl");
const elApiKey = document.getElementById("apiKey");
const elStatus = document.getElementById("status");

function tampilkan(pesan, kelas = "") {
  elStatus.className = kelas;
  elStatus.textContent = pesan;
}

function baseUrlBersih() {
  return (elBaseUrl.value || BAWAAN.apiBaseUrl).trim().replace(/\/+$/, "");
}

/**
 * Manifest hanya mencantumkan host API yang umum dipakai. Untuk host lain,
 * izin diminta saat dibutuhkan supaya service worker boleh memanggilnya.
 */
async function pastikanIzinHost(baseUrl) {
  let origin;
  try {
    origin = `${new URL(baseUrl).origin}/*`;
  } catch {
    throw new Error("Alamat API tidak valid.");
  }

  if (await chrome.permissions.contains({ origins: [origin] })) return;
  if (await chrome.permissions.request({ origins: [origin] })) return;
  throw new Error(`Izin akses ke ${origin} tidak diberikan.`);
}

async function muat() {
  const konfig = await chrome.storage.local.get(BAWAAN);
  elBaseUrl.value = konfig.apiBaseUrl || BAWAAN.apiBaseUrl;
  elApiKey.value = konfig.apiKey || "";
}

async function simpan() {
  const baseUrl = baseUrlBersih();
  try {
    await pastikanIzinHost(baseUrl);
  } catch (err) {
    tampilkan(err.message, "gagal");
    return;
  }

  await chrome.storage.local.set({
    apiBaseUrl: baseUrl,
    apiKey: elApiKey.value.trim(),
  });
  elBaseUrl.value = baseUrl;
  tampilkan("Tersimpan.", "ok");
}

async function uji() {
  tampilkan("Menghubungi API...");
  try {
    await pastikanIzinHost(baseUrlBersih());
  } catch (err) {
    tampilkan(err.message, "gagal");
    return;
  }

  const balasan = await chrome.runtime.sendMessage({
    tipe: "api",
    jalur: "/health",
    metode: "GET",
    // Menguji nilai yang sedang diisi, belum tentu yang tersimpan.
    konfig: { apiBaseUrl: baseUrlBersih(), apiKey: elApiKey.value.trim() },
  });

  if (!balasan?.ok) {
    tampilkan(`Gagal: ${balasan?.pesan || "tidak ada balasan"}`, "gagal");
    return;
  }

  const h = balasan.data;
  tampilkan(
    `Terhubung. Status: ${h.status}, database: ${h.database} (${
      h.database_terhubung ? "tersambung" : "TIDAK tersambung"
    })${h.pesan ? `\n${h.pesan}` : ""}`,
    h.database_terhubung ? "ok" : "gagal",
  );
}

document.getElementById("simpan").addEventListener("click", simpan);
document.getElementById("uji").addEventListener("click", uji);
muat();
