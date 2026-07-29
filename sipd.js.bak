const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJTSVBEX0FVVEhfU0VSVklDRSIsInN1YiI6IjI3MTg1LjcwIiwiZXhwIjoxNzcwNDA0Mjc5LCJpYXQiOjE3NzAxODgyNzksInRhaHVuIjoyMDI1LCJpZF91c2VyIjoyNzE4NSwiaWRfZGFlcmFoIjo3MCwia29kZV9wcm92aW5zaSI6IjMzIiwia29kZV9kZG4iOiIzMy43NiIsImlkX3NrcGQiOjQ3NSwiaWRfcm9sZSI6MTAsImlkX3BlZ2F3YWkiOjY1ODk0OCwic3ViX2RvbWFpbl9kYWVyYWgiOiJ0ZWdhbCJ9.BEXjxyVOS_itLcxQ4IPI1omCoF6xZnNvC6wpmSLwQg0"; 

const urllocal = "http://localhost:3000/tblra";


function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null; 
}

const namaBulan = [
  "",
  "Januari",
  "Februari",
  "Maret",
  "April",
  "Mei",
  "Juni",
  "Juli",
  "Agustus",
  "September",
  "Oktober",
  "November",
  "Desember"
];

const parentElement = document.querySelector('.nav-tools.flex.items-center');

const newDiv = document.createElement('div');
const button = document.createElement('button');
button.textContent = 'Sinkronkan Simlaba';
button.className = 'btn undefined btn inline-flex justify-center bg-danger-500 text-white';
button.setAttribute('type', 'button');
button.setAttribute('data-bs-toggle', 'tooltip');
button.setAttribute('data-bs-placement', 'top');
button.setAttribute('title', 'Sinkronkan Realisasi Keuangan ke Simlaba');
button.innerHTML = '<img src="https://cdn-icons-png.flaticon.com/128/2512/2512713.png" width="32" height="32">';
newDiv.appendChild(button);

const newDiv2 = document.createElement('div');
const button2 = document.createElement('button');
button2.textContent = 'Sinkronkan Simlaba Semua OPD';
button2.className = 'btn undefined btn inline-flex justify-center bg-success-500 text-white';
button2.setAttribute('type', 'button');
button2.setAttribute('data-bs-toggle', 'tooltip');
button2.setAttribute('data-bs-placement', 'top');
button2.setAttribute('title', 'Sinkronkan Realisasi Keuangan Semua OPD ke Simlaba');
button2.innerHTML = '<img src="https://cdn-icons-png.flaticon.com/128/2512/2512713.png" width="32" height="32">';
newDiv2.appendChild(button2);

parentElement.prepend(newDiv);    
parentElement.prepend(newDiv2);

button.addEventListener('click', () => {

  const modal = document.createElement('div');
  modal.classList.add('modal-backdrop');
  modal.style.position = 'fixed';
  modal.style.top = '0';
  modal.style.left = '0';
  modal.style.width = '100%';
  modal.style.height = '100%';
  modal.style.background = 'rgba(0, 0, 0, 0.5)';
  modal.style.display = 'flex';
  modal.style.justifyContent = 'center';
  modal.style.alignItems = 'center';
  modal.style.zIndex = '1000';

  
  const box = document.createElement('div');
  box.classList.add('modal-box');
  box.style.background = '#fff';
  box.style.padding = '20px';
  box.style.borderRadius = '10px';
  box.style.minWidth = '300px';
  box.style.maxWidth = '90%';
  box.style.boxShadow = '0 0 10px rgba(0,0,0,0.3)';
  box.style.animation = 'fadeIn 0.06s ease';

  
  box.innerHTML = `
    <h3>Sinkronisasi SIPD & Simlaba</h3>
    <p>----------------------------</p>
      <form id="syncSimlabaForm">
        <label for="syncbulan">Pilih Bulan:</label>
        <select name="syncbulan" id="syncbulan" required>
          <option value="1">Januari</option>
          <option value="2">Februari</option>
          <option value="3">Maret</option>
          <option value="4">April</option>
          <option value="5">Mei</option>
          <option value="6">Juni</option>
          <option value="7">Juli</option>
          <option value="8">Agustus</option>
          <option value="9">September</option>
          <option value="10">Oktober</option>
          <option value="11">November</option>
          <option value="12">Desember</option>
        </select>
        <p>----------------------------</p>
        <br/>
        <button id="closeModalBtn" class="btn inline-flex justify-center bg-danger-500 text-white">Tutup</button> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<button type="submit" class="btn inline-flex justify-center bg-success-500 text-white">Proses</button> 
      </form>
      <div id="syncLoaderAnim" style="display:none;"><img src="https://cdn.dribbble.com/userupload/24354714/file/original-0252e0e6dca0c37238eff2620cf51653.gif" style="width:260px;height:210px">  </div>
      <div id="syncNotif" style="display:none;">AAAAAAA</div>
  `;

  
  modal.appendChild(box);
  document.body.appendChild(modal);

  
  document.getElementById('closeModalBtn').addEventListener('click', () => {
    document.body.removeChild(modal);
  });

 
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      document.body.removeChild(modal);
    }
  });

  document.getElementById('syncSimlabaForm').addEventListener('submit', function(event) {
    event.preventDefault(); 

    document.getElementById("syncLoaderAnim").style.display = "block";
    document.getElementById("syncSimlabaForm").style.display = "none";
  
    const formData = new FormData(this);
    const tbulan = document.getElementById('syncbulan').value;
    
    const xtoken = getCookie('X-SIPD-PU-TK');
    const xurl = `https://service.sipd.kemendagri.go.id/pengeluaran/strict/lpj/adm-fungs/0?type=SKPD&id_pegawai=0&bulan=${tbulan}`;
    
  
    const xhr = new XMLHttpRequest();
    xhr.open("GET", xurl, true);
    xhr.setRequestHeader("accept", "application/json");
    xhr.setRequestHeader("authorization", `Bearer ${xtoken}`);
    
    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        const obj = JSON.parse(xhr.responseText);
        console.log("Response:",obj);
        const ptahun = obj.tahun;
        const remote_url = `https://monevrkpd.tegalkota.go.id/emonev${ptahun}/api/sipd/updaerealisasikeuangan`;
        
                fetch(remote_url, {
                  method: 'POST',
                  headers: {
                    "Content-Type": 'application/json',
                    "Authorization": `Bearer ${token}`,
                  },
                  body: JSON.stringify({
                    'jumlah_sd_saat_ini':obj.pembukuan1[0].jumlah_sd_saat_ini,
                    'tahun' : ptahun,
                    'bulan': tbulan,
                    'kode_pd':obj.kode_skpd,
                    'xdata': obj.pembukuan2,
                    'chrversion' : '1.4'
                  })
                })
                .then(response => {
                  if (!response.ok) {
                    throw new Error('Network response was not ok');
                  }
                  return response.json(); 
                })
                .then(data => {
                  namaBulanIni = namaBulan[tbulan];
                  console.log('Success:', data);
                  document.getElementById("syncLoaderAnim").style.display = "none";
                  document.getElementById("syncSimlabaForm").style.display = "none";
                  document.getElementById("syncNotif").style.display = "block";
                  document.getElementById("syncNotif").innerHTML = `Data realisasi keuangan bulan <b> ${namaBulanIni} ${ptahun} </b>berhasil diunduh ke Simlaba :<b> Rp.  ${data.total}</b>`;
                })
                .catch(error => {
                  console.error('Error:', error);
                  console.log('Success:', data);
                  document.getElementById("syncLoaderAnim").style.display = "none";
                  document.getElementById("syncSimlabaForm").style.display = "none";
                  document.getElementById("syncNotif").style.display = "block";
                  document.getElementById("syncNotif").innerHTML = "ERROR BOS";
                });
      } else {
        console.error(`HTTP error ${xhr.status}: ${xhr.statusText}`);
        document.getElementById("syncLoaderAnim").style.display = "none";
        document.getElementById("syncSimlabaForm").style.display = "none";
        document.getElementById("syncNotif").style.display = "block";
        document.getElementById("syncNotif").innerHTML = "ERROR BOS";
      }
    };


    xhr.onerror = function () {
      console.error("Network error occurred");
      document.getElementById("syncLoaderAnim").style.display = "none";
                  document.getElementById("syncSimlabaForm").style.display = "none";
                  document.getElementById("syncNotif").style.display = "block";
                  document.getElementById("syncNotif").innerHTML = "ERROR BOS";
    };
    xhr.send();


  });

});



function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseIdNumber(str) {
  if (!str) return 0;

  return Number(
    str
      .replace(/\./g, "") // hapus pemisah ribuan
      .replace(",", "."), // ganti koma jadi titik desimal
  );
}

async function pushData(xdata) {
  const xd = await fetch("http://localhost:3000/tblra2", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      // kalau perlu auth:
      // "Authorization": "Bearer " + token,
    },
    body: JSON.stringify(xdata),
  });
}

async function runLoopSipd(opds, xtoken) {
  for (const idpd of opds) {
    const xurl = `https://service.sipd.kemendagri.go.id/aklap/api/report/cetak-lra-per-program?searchparams=%7B%22filter%22:1,%22bulan%22:12,%22triwulan%22:1,%22semester%22:1,%22id_skpd%22:${idpd},%22uraian%22:null,%22klasifikasi%22:null,%22formatFile%22:%22preview%22,%22is_combine%22:%22skpd%22%7D&dateFrom=2025-01-01&dateTo=2025-12-31`;
    console.log (idpd);
    const res = await fetch(xurl, {
      method: "GET",
      headers: {
        accept: "application/json",
        authorization: `Bearer ${xtoken}`,
      },
    });
    const obj = await res.json();
    const result = [];
    const headers = [
      "kode1",
      "kode2",
      "kode3",
      "kode4",
      "uraian",
      "operasi_angg",
      "operasi_real",
      "modal_angg",
      "modal_real",
      "tt_angg",
      "tt_real",
      "tf_angg",
      "tf_real",
    ];

    let index = 0;
    const htmlString = obj.data;
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlString, "text/html");
    const table =
      doc.querySelector("table.tb-content") || doc.querySelector("table");
    const rows = table.querySelectorAll("tbody tr, tr");
    rows.forEach((tr, index) => {
      const cells = tr.querySelectorAll("td");

      // Skip baris yang tidak punya data kolom
      if (cells.length === 0) return;

      // Skip baris yang pakai merge cell
      if (tr.querySelector("td[colspan], td[rowspan]")) return;

      // Optional: pastikan jumlah kolom minimal sesuai header
      if (cells.length < headers.length) return;

      const objx = { idopd: Number(idpd) };
      cells.forEach((td, i) => {
        const key = headers[i] || `col_${i + 1}`;
        const val = td.textContent.trim();

        if (i > 4) {
          objx[key] = parseIdNumber(val);
        } else {
          objx[key] = val;
        }
      });

      result.push(objx);
    });

    const psdata = await pushData(result);

    console.log(psdata);

    await sleep(2000);
  }
}


button2.addEventListener("click", () => {
  const modal = document.createElement("div");
  modal.classList.add("modal-backdrop");
  modal.style.position = "fixed";
  modal.style.top = "0";
  modal.style.left = "0";
  modal.style.width = "100%";
  modal.style.height = "95%";
  modal.style.background = "rgba(0, 0, 0, 0.5)";
  modal.style.display = "flex";
  modal.style.justifyContent = "center";
  modal.style.alignItems = "center";
  modal.style.zIndex = "1000";

  const box = document.createElement("div");
  box.classList.add("modal-box");
  box.style.background = "#fff";
  box.style.padding = "20px";
  box.style.borderRadius = "10px";
  box.style.minWidth = "300px";
  box.style.maxWidth = "90%";
  box.style.boxShadow = "0 0 10px rgba(0,0,0,0.3)";
  box.style.animation = "fadeIn 0.06s ease";

  box.innerHTML = `
    <h3>Sinkronisasi SIPD & Simlaba</h3>
    <p>----------------------------</p>
      <form id="syncSimlabaForm">
        <label for="syncbulan">Pilih Bulan:</label>
        <select name="syncbulan" id="syncbulan" required>
          <option value="1">Januari</option>
          <option value="2">Februari</option>
          <option value="3">Maret</option>
          <option value="4">April</option>
          <option value="5">Mei</option>
          <option value="6">Juni</option>
          <option value="7">Juli</option>
          <option value="8">Agustus</option>
          <option value="9">September</option>
          <option value="10">Oktober</option>
          <option value="11">November</option>
          <option value="12">Desember</option>
        </select>
        <br/>
        <div id="dtable"  style="height:450px;overflow-y: auto;overflow-x: hidden;">
        <table class="table table-striped table-hover">
                <thead>
                    <tr class="table-danger">
                        <th style="width: 40px;">
                            <input type="checkbox" id="checkAll">
                        </th>
                        <th scope="col" style="width: 50px;">#</th>
                        <th scope="col" style="width: 0px;">Kode</th>
                        <th scope="col">OPD</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>1</td>
                        <td>458</td>
                        <td>Dinas Pendidikan dan Kebudayaan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>2</td>
                        <td>890</td>
                        <td>Sekolah Menengah Pertama Negeri 1</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>3</td>
                        <td>891</td>
                        <td>Sekolah Menengah Pertama Negeri 2</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>4</td>
                        <td>892</td>
                        <td>Sekolah Menengah Pertama Negeri 3</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>5</td>
                        <td>894</td>
                        <td>Sekolah Menengah Pertama Negeri 4</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>6</td>
                        <td>895</td>
                        <td>Sekolah Menengah Pertama Negeri 5</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>7</td>
                        <td>896</td>
                        <td>Sekolah Menengah Pertama Negeri 6</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>8</td>
                        <td>897</td>
                        <td>Sekolah Menengah Pertama Negeri 7</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>9</td>
                        <td>898</td>
                        <td>Sekolah Menengah Pertama Negeri 8</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>10</td>
                        <td>899</td>
                        <td>Sekolah Menengah Pertama Negeri 9</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>11</td>
                        <td>900</td>
                        <td>Sekolah Menengah Pertama Negeri 10</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>12</td>
                        <td>901</td>
                        <td>Sekolah Menengah Pertama Negeri 11</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>13</td>
                        <td>902</td>
                        <td>Sekolah Menengah Pertama Negeri 12</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>14</td>
                        <td>903</td>
                        <td>Sekolah Menengah Pertama Negeri 13</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>15</td>
                        <td>904</td>
                        <td>Sekolah Menengah Pertama Negeri 14</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>16</td>
                        <td>905</td>
                        <td>Sekolah Menengah Pertama Negeri 15</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>17</td>
                        <td>906</td>
                        <td>Sekolah Menengah Pertama Negeri 17</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>18</td>
                        <td>907</td>
                        <td>Sekolah Menengah Pertama Negeri 18</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>19</td>
                        <td>908</td>
                        <td>Sekolah Menengah Pertama Negeri 19</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>20</td>
                        <td>9160</td>
                        <td>Sekolah Menengah Pertama Negeri 1 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>21</td>
                        <td>9161</td>
                        <td>Sekolah Menengah Pertama Negeri 2 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>22</td>
                        <td>9162</td>
                        <td>Sekolah Menengah Pertama Negeri 3 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>23</td>
                        <td>9163</td>
                        <td>Sekolah Menengah Pertama Negeri 4 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>24</td>
                        <td>9164</td>
                        <td>Sekolah Menengah Pertama Negeri 5 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>25</td>
                        <td>9165</td>
                        <td>Sekolah Menengah Pertama Negeri 6 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>26</td>
                        <td>9166</td>
                        <td>Sekolah Menengah Pertama Negeri 7 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>27</td>
                        <td>9167</td>
                        <td>Sekolah Menengah Pertama Negeri 8 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>28</td>
                        <td>9168</td>
                        <td>Sekolah Menengah Pertama Negeri 9 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>29</td>
                        <td>9169</td>
                        <td>Sekolah Menengah Pertama Negeri 10 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>30</td>
                        <td>9170</td>
                        <td>Sekolah Menengah Pertama Negeri 11 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>31</td>
                        <td>9171</td>
                        <td>Sekolah Menengah Pertama Negeri 12 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>32</td>
                        <td>9172</td>
                        <td>Sekolah Menengah Pertama Negeri 13 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>33</td>
                        <td>9173</td>
                        <td>Sekolah Menengah Pertama Negeri 14 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>34</td>
                        <td>9174</td>
                        <td>Sekolah Menengah Pertama Negeri 15 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>35</td>
                        <td>17713</td>
                        <td>Sekolah Menengah Pertama Negeri 16</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>36</td>
                        <td>17714</td>
                        <td>Sekolah Menengah Pertama Negeri 16 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>37</td>
                        <td>9175</td>
                        <td>Sekolah Menengah Pertama Negeri 17 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>38</td>
                        <td>9176</td>
                        <td>Sekolah Menengah Pertama Negeri 18 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>39</td>
                        <td>9177</td>
                        <td>Sekolah Menengah Pertama Negeri 19 (BOS)</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>40</td>
                        <td>459</td>
                        <td>Dinas Kesehatan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>41</td>
                        <td>557</td>
                        <td>Klinik Paru Masyarakat</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>42</td>
                        <td>558</td>
                        <td>Puskesmas Tegal Barat</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>43</td>
                        <td>559</td>
                        <td>Puskesmas Debong Lor</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>44</td>
                        <td>560</td>
                        <td>Puskesmas Tegal Timur</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>45</td>
                        <td>561</td>
                        <td>Puskesmas Slerok</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>46</td>
                        <td>562</td>
                        <td>Puskesmas Tegal Selatan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>47</td>
                        <td>563</td>
                        <td>Puskesmas Bandung</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>48</td>
                        <td>564</td>
                        <td>Puskesmas Margadana</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>49</td>
                        <td>565</td>
                        <td>Puskesmas Kaligangsa</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>50</td>
                        <td>9178</td>
                        <td>BLUD Klinik Paru Masyarakat</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>51</td>
                        <td>9179</td>
                        <td>BLUD Puskesmas Tegal Barat</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>52</td>
                        <td>9180</td>
                        <td>BLUD Puskesmas Debong Lor</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>53</td>
                        <td>9181</td>
                        <td>BLUD Puskesmas Tegal Timur</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>54</td>
                        <td>9182</td>
                        <td>BLUD Puskesmas Slerok</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>55</td>
                        <td>9183</td>
                        <td>BLUD Puskesmas Tegal Selatan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>56</td>
                        <td>9184</td>
                        <td>BLUD Puskesmas Bandung</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>57</td>
                        <td>9185</td>
                        <td>BLUD Puskesmas Margadana</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>58</td>
                        <td>9186</td>
                        <td>BLUD Puskesmas Kaligangsa</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>59</td>
                        <td>534</td>
                        <td>RSUD Kardinah</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>60</td>
                        <td>9188</td>
                        <td>BLUD RSUD Kardinah</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>61</td>
                        <td>460</td>
                        <td>Dinas Pekerjaan Umum dan Penataan Ruang</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>62</td>
                        <td>461</td>
                        <td>Dinas Perumahan dan Kawasan Permukiman</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>63</td>
                        <td>462</td>
                        <td>Satuan Polisi Pamong Praja</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>64</td>
                        <td>546</td>
                        <td>Badan Penanggulangan Bencana Daerah</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>65</td>
                        <td>463</td>
                        <td>Dinas Sosial</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>66</td>
                        <td>464</td>
                        <td>Dinas Tenaga Kerja dan Perindustrian</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>67</td>
                        <td>465</td>
                        <td>Dinas Lingkungan Hidup</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>68</td>
                        <td>467</td>
                        <td>Dinas Kependudukan dan Pencatatan Sipil</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>69</td>
                        <td>466</td>
                        <td>Dinas Pengendalian Penduduk & KB, Pemberdayaan Perempuan & Perlindungan Anak</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>70</td>
                        <td>468</td>
                        <td>Dinas Perhubungan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>71</td>
                        <td>469</td>
                        <td>Dinas Komunikasi dan Informatika</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>72</td>
                        <td>470</td>
                        <td>Dinas Koperasi, Usaha Kecil Menengah, dan Perdagangan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>73</td>
                        <td>471</td>
                        <td>Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>74</td>
                        <td>472</td>
                        <td>Dinas Kepemudaan dan Olah Raga, dan Pariwisata</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>75</td>
                        <td>473</td>
                        <td>Dinas Kearsipan dan Perpustakaan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>76</td>
                        <td>474</td>
                        <td>Dinas Kelautan dan Perikanan, Pertanian dan Pangan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>77</td>
                        <td>548</td>
                        <td>Bagian Umum</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>78</td>
                        <td>550</td>
                        <td>Bagian Organisasi</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>79</td>
                        <td>553</td>
                        <td>Bagian Hukum</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>80</td>
                        <td>545</td>
                        <td>Bagian Protokol dan Komunikasi Pimpinan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>81</td>
                        <td>549</td>
                        <td>Bagian Pemerintahan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>82</td>
                        <td>551</td>
                        <td>Bagian Kesejahteraan Rakyat</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>83</td>
                        <td>552</td>
                        <td>Bagian Perekonomian</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>84</td>
                        <td>555</td>
                        <td>Bagian Pengadaan Barang dan Jasa, dan Administrasi Pembangunan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>85</td>
                        <td>535</td>
                        <td>Sekretariat DPRD</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>86</td>
                        <td>475</td>
                        <td>Badan Perencanaan Pembangunan, Riset dan Inovasi Daerah</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>87</td>
                        <td>476</td>
                        <td>Badan Keuangan Daerah</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>88</td>
                        <td>477</td>
                        <td>Badan Kepegawaian Dan Pengembangan Sumber Daya Manusia</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>89</td>
                        <td>478</td>
                        <td>Inspektorat</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>90</td>
                        <td>479</td>
                        <td>Kecamatan Tegal Timur</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>91</td>
                        <td>566</td>
                        <td>Kelurahan Kejambon</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>92</td>
                        <td>567</td>
                        <td>Kelurahan Slerok</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>93</td>
                        <td>568</td>
                        <td>Kelurahan Panggung</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>94</td>
                        <td>569</td>
                        <td>Kelurahan Mangkukusuman</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>95</td>
                        <td>570</td>
                        <td>Kelurahan Mintaragen</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>96</td>
                        <td>481</td>
                        <td>Kecamatan Tegal Barat</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>97</td>
                        <td>571</td>
                        <td>Kelurahan Pesurungan Kidul</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>98</td>
                        <td>572</td>
                        <td>Kelurahan Debong Lor</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>99</td>
                        <td>573</td>
                        <td>Kelurahan Kemandungan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>100</td>
                        <td>574</td>
                        <td>Kelurahan Pekauman</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>101</td>
                        <td>575</td>
                        <td>Kelurahan Kraton</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>102</td>
                        <td>576</td>
                        <td>Kelurahan Tegalsari</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>103</td>
                        <td>577</td>
                        <td>Kelurahan Muarareja</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>104</td>
                        <td>482</td>
                        <td>Kecamatan Tegal Selatan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>105</td>
                        <td>578</td>
                        <td>Kelurahan Kalinyamat Wetan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>106</td>
                        <td>579</td>
                        <td>Kelurahan Bandung</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>107</td>
                        <td>580</td>
                        <td>Kelurahan Debong Kidul</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>108</td>
                        <td>587</td>
                        <td>Kelurahan Tunon</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>109</td>
                        <td>588</td>
                        <td>Kelurahan Keturen</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>110</td>
                        <td>589</td>
                        <td>Kelurahan Debong Kulon</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>111</td>
                        <td>590</td>
                        <td>Kelurahan Debong Tengah</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>112</td>
                        <td>591</td>
                        <td>Kelurahan Randugunting</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>113</td>
                        <td>483</td>
                        <td>Kecamatan Margadana</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>114</td>
                        <td>592</td>
                        <td>Kelurahan Kaligangsa</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>115</td>
                        <td>593</td>
                        <td>Kelurahan Krandon</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>116</td>
                        <td>594</td>
                        <td>Kelurahan Cabawan</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>117</td>
                        <td>595</td>
                        <td>Kelurahan Margadana</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>118</td>
                        <td>596</td>
                        <td>Kelurahan Kalinyamat Kulon</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>119</td>
                        <td>597</td>
                        <td>Kelurahan Sumurpanggang</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>120</td>
                        <td>598</td>
                        <td>Kelurahan Pesurungan Lor</td>
                    </tr>
                    <tr>
                        <td><input type='checkbox' class='row-check'></td>
                        <td>121</td>
                        <td>480</td>
                        <td>Badan Kesatuan Bangsa dan Politik</td>
                    </tr>


                </tbody>
            </table>
            </div>

        <p>----------------------------</p>
        <br/>
        <button id="closeModalBtn" class="btn inline-flex justify-center bg-danger-500 text-white">Tutup</button> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<button type="submit" class="btn inline-flex justify-center bg-success-500 text-white">Proses</button> 
      </form>
      <div id="syncLoaderAnim" style="display:none;"><img src="https://cdn.dribbble.com/userupload/24354714/file/original-0252e0e6dca0c37238eff2620cf51653.gif" style="width:260px;height:210px">  </div>
      <div id="syncNotif" style="display:none;">AAAAAAA</div>
  `;

  modal.appendChild(box);
  document.body.appendChild(modal);

  document.getElementById("closeModalBtn").addEventListener("click", () => {
    document.body.removeChild(modal);
  });

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      document.body.removeChild(modal);
    }
  });

  document.getElementById("checkAll").addEventListener("change", function () {
          document.querySelectorAll(".row-check").forEach((cb) => {
            cb.checked = this.checked;
          });
        });

  document
    .getElementById("syncSimlabaForm")
    .addEventListener("submit", function (event) {
      event.preventDefault();

      var opds = [];

      document.querySelectorAll(".row-check:checked").forEach((cb) => {
        const row = cb.closest("tr");
        const kode = row.children[2].textContent.trim(); // kolom Kode
        opds.push(kode);
      });

      //const formData = new FormData(this);
      const tbulan = document.getElementById("syncbulan").value;

      const result = [];

      const xtoken = getCookie("X-SIPD-PU-TK");

      runLoopSipd(opds, xtoken);
    });
});
