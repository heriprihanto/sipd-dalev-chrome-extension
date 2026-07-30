/**
 * Service worker: perantara antara content script dan REST API.
 *
 * Halaman SIPD dilayani lewat HTTPS, sehingga fetch langsung dari content
 * script ke API HTTP diblokir browser (mixed content). Permintaan dari service
 * worker extension tidak terkena aturan itu dan juga tidak terkena CORS,
 * asalkan host API tercantum di host_permissions manifest.
 */

const KONFIG_BAWAAN = {
  apiBaseUrl: "http://localhost:8000",
  apiKey: "",
};

async function konfigApi() {
  const tersimpan = await chrome.storage.local.get(KONFIG_BAWAAN);
  return {
    apiBaseUrl: (tersimpan.apiBaseUrl || KONFIG_BAWAAN.apiBaseUrl).replace(
      /\/+$/,
      "",
    ),
    apiKey: tersimpan.apiKey || "",
  };
}

/** Pesan error yang bisa dibaca pengguna dari respons FastAPI. */
function pesanGagal(status, statusText, data) {
  const detail = data?.detail;
  if (typeof detail === "string") return `HTTP ${status}: ${detail}`;
  if (Array.isArray(detail) && detail.length) {
    const pertama = detail[0];
    return `HTTP ${status}: ${pertama.msg || JSON.stringify(pertama)}`;
  }
  return `HTTP ${status} ${statusText}`;
}

async function panggilApi({ jalur, metode = "POST", body, konfig }) {
  // `konfig` dipakai halaman Opsi untuk menguji alamat yang belum disimpan.
  const tersimpan = await konfigApi();
  const apiBaseUrl = (konfig?.apiBaseUrl || tersimpan.apiBaseUrl).replace(
    /\/+$/,
    "",
  );
  const apiKey = konfig?.apiKey ?? tersimpan.apiKey;

  const headers = { "content-type": "application/json" };
  if (apiKey) headers["x-api-key"] = apiKey;

  let res;
  try {
    res = await fetch(`${apiBaseUrl}${jalur}`, {
      method: metode,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (err) {
    throw new Error(
      `Tidak bisa menghubungi API di ${apiBaseUrl} (${err.message}). ` +
        "Pastikan server REST API berjalan dan alamatnya benar di halaman Opsi extension.",
    );
  }

  const teks = await res.text();
  let data = null;
  if (teks) {
    try {
      data = JSON.parse(teks);
    } catch {
      data = { detail: teks.slice(0, 300) };
    }
  }

  if (!res.ok) throw new Error(pesanGagal(res.status, res.statusText, data));
  return data;
}

chrome.runtime.onMessage.addListener((pesan, _pengirim, balas) => {
  if (pesan?.tipe !== "api") return false;

  panggilApi(pesan)
    .then((data) => balas({ ok: true, data }))
    .catch((err) => balas({ ok: false, pesan: err.message }));

  // true = balasan dikirim secara asinkron.
  return true;
});
