/**
 * SISTEM INFORMASI HIDROGEOLOGI KARST NTT
 * Developer: B. Pati Kondanglimu, ST & Gemini
 * Tahun: 2026
 */

// 1. Fungsi Logika Perhitungan Neraca Air Permukaan
function hitungNeracaAir(curahHujan, evapotranspirasi) {
    const hasil = curahHujan - evapotranspirasi;
    if (hasil < 0) {
        return {
            nilai: Math.abs(hasil).toFixed(2),
            status: "Defisit Air (Kekeringan)",
            rekomendasi: "Tingkat evapotranspirasi tinggi. Diperlukan optimalisasi pemanfaatan air tanah bawah permukaan (aquifer storage)."
        };
    } else {
        return {
            nilai: hasil.toFixed(2),
            status: "Surplus Air (Potensi Infiltrasi)",
            rekomendasi: "Potensi tinggi untuk perkolasi alamiah menuju sistem sungai bawah tanah karst."
        };
    }
}

// 2. Fungsi Logika Perhitungan Cadangan Volume Air Tanah
function hitungAquiferStorage(luasAreaM2, tebalAkuiferM, porositasSekunder) {
    // Rumus hidrogeologi volume efektif: V = A * H * Sy
    const volumeAirM3 = luasAreaM2 * tebalAkuiferM * porositasSekunder;
    const volumeAirLiter = volumeAirM3 * 1000;
    
    return {
        volumeM3: volumeAirM3,
        volumeLiter: volumeAirLiter
    };
}

// ==========================================
// INTERAKSI FRONT-END / JEMBATAN TOMBOL UI
// ==========================================

function prosesNeracaAir() {
    const P = parseFloat(document.getElementById('inputP').value);
    const ET = parseFloat(document.getElementById('inputET').value);
    const boxHasil = document.getElementById('resultNeraca');
    
    if (isNaN(P) || isNaN(ET)) {
        alert("Mohon masukkan angka Curah Hujan (P) dan Evapotranspirasi (ET) dengan benar.");
        return;
    }
    
    const analisis = hitungNeracaAir(P, ET);
    boxHasil.classList.remove('hidden');
    boxHasil.innerHTML = `
        <p class="font-bold text-karst-accent">Hasil Analisis:</p>
        <p class="mt-1">Nilai Selisih: <strong>${analisis.nilai} mm</strong></p>
        <p>Status Kawasan: <span class="px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded font-semibold">${analisis.status}</span></p>
        <p class="mt-2 text-gray-500 italic text-[11px]">Rekomendasi: ${analisis.rekomendasi}</p>
    `;
}

function prosesAquifer() {
    const area = parseFloat(document.getElementById('inputArea').value);
    const tebal = parseFloat(document.getElementById('inputTebal').value);
    const porositas = parseFloat(document.getElementById('inputPorositas').value);
    const boxHasil = document.getElementById('resultAquifer');
    
    if (isNaN(area) || isNaN(tebal)) {
        alert("Mohon lengkapi parameter Luas Area dan Tebal Akuifer.");
        return;
    }
    
    const storage = hitungAquiferStorage(area, tebal, porositas);
    boxHasil.classList.remove('hidden');
    boxHasil.innerHTML = `
        <p class="font-bold text-karst-savana">Estimasi Cadangan Lapisan:</p>
        <p class="mt-1">Volume Air Bebas: <strong>${storage.volumeM3.toLocaleString('id-ID')} m³</strong></p>
        <p>Kapasitas Setara: <strong>${storage.volumeLiter.toLocaleString('id-ID')} Liter</strong></p>
        <p class="mt-2 text-[10px] text-gray-400 italic">*Perhitungan menggunakan konstanta ruang pori sekunder batuan makro-karst.</p>
    `;
}
