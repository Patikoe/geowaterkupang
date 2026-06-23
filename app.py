import streamlit as st
import pandas as pd
import numpy as np
import math

# Set Konfigurasi Halaman Dashboard
st.set_page_config(page_title="GeoWater-IQ: Sistem Terintegrasi Kualitas Air", layout="wide")

st.title("🌊 GeoWater-IQ")
st.subheader("Sistem Informasi Hidro-Karst & Analisis Kualitas Air Terpadu")
st.write("Aplikasi Multifungsi Analisis Mutu, Peruntukan, Kerentanan Karst, dan Rekomendasi Kebijakan Air.")
st.markdown("---")

# ==========================================
# SIDEBAR: INPUT DATA & PARAMETER
# ==========================================
st.sidebar.header("📥 Input Data Kualitas Air")
sample_name = st.sidebar.text_input("Nama Titik / Lokasi Sampel", "Sumur Gali Alak - Titik 09")
kelurahan = st.sidebar.selectbox("Kelurahan", ["Alak", "Nunbaun Sabu", "Namosain", "Batuplat", "Penkase Oeleta", "Manutapen"])

st.sidebar.markdown("### 🔬 Hasil Pengujian Laboratorium")
ph = st.sidebar.slider("pH Air", 0.0, 14.0, 7.4, 0.1)
tds = st.sidebar.number_input("TDS (mg/L)", value=710)
kesadahan = st.sidebar.number_input("Kesadahan (CaCO3 dalam mg/L)", value=520)
coliform = st.sidebar.number_input("Total Coliform (CFU/100ml)", value=35)
bod = st.sidebar.number_input("BOD (mg/L)", value=6.5)
cod = st.sidebar.number_input("COD (mg/L)", value=22.0)
nitrat = st.sidebar.number_input("Nitrat (NO3-N dalam mg/L)", value=12.5)

st.sidebar.markdown("### 🪨 Parameter Hidrogeologi & Spasial (Karst)")
jarak_ponor = st.sidebar.number_input("Jarak ke Ponor / Sinkhole terdekat (Meter)", value=85)
kedalaman_air = st.sidebar.number_input("Kedalaman Muka Air Tanah (Meter)", value=15)

# ==========================================
# CORE ENGINE: PERHITUNGAN & PROSES
# ==========================================

# 1. Perhitungan Indeks Pencemaran (IP) - [MODUL 1]
# Baku Mutu Kelas 2 (PP 22/2021 & Permenkes Sanitasi)
L_ph_min, L_ph_max = 6.5, 8.5
L_tds = 1000.0
L_kesadahan = 500.0
L_coliform = 50.0

# Hitung Rasio Ci/Li
r_ph = 1.0 if L_ph_min <= ph <= L_ph_max else max(L_ph_min/ph, ph/L_ph_max)
r_tds = tds / L_tds
r_kesadahan = kesadahan / L_kesadahan
r_coliform = coliform / L_coliform

ratios = [r_ph, r_tds, r_kesadahan, r_coliform]
ratios_adjusted = []

for r in ratios:
    if r > 1.0:
        r_adj = 1.0 + 5.0 * math.log(r)
    else:
        r_adj = r
    ratios_adjusted.append(r_adj)

r_max = max(ratios_adjusted)
r_avg = sum(ratios_adjusted) / len(ratios_adjusted)
ip_score = math.sqrt((r_max**2 + r_avg**2) / 2.0)

if ip_score <= 1.0:
    status_mutu = "Memenuhi Baku Mutu (Baik)"
    color_status = "green"
elif ip_score <= 5.0:
    status_mutu = "Tercemar Ringan"
    color_status = "orange"
elif ip_score <= 10.0:
    status_mutu = "Tercemar Sedang"
    color_status = "red"
else:
    status_mutu = "Tercemar Berat"
    color_status = "purple"

# Indeks Kualitas Air (IKA) Simp. Skala 0-100
ika_score = max(0, min(100, int(100 - (ip_score * 8))))

# 2. Perhitungan Kerentanan Spasial DRASTIC & Karst - [MODUL 4 & 5]
# Modifikasi sederhana indeks kerentanan berbasis parameter input
drastic_score = (kedalaman_air * 2) + (5 if jarak_ponor < 100 else 2)
if jarak_ponor < 100:
    kerentanan_status = "Sangat Tinggi (Zona Kerentanan Karst Akut)"
    color_vun = "red"
    travel_time = "Cepat (< 24 Jam) via Porositas Sekunder"
elif jarak_ponor < 500:
    kerentanan_status = "Sedang"
    color_vun = "orange"
    travel_time = "Moderat (2 - 5 Hari)"
else:
    kerentanan_status = "Rendah"
    color_vun = "green"
    travel_time = "Lambat (> 10 Hari)"


# ==========================================
# LAYOUT UTAMA DASHBOARD INTERAKTIF
# ==========================================

tabs = st.tabs([
    "🎯 1 & 2. Status Mutu & Kelayakan", 
    "🔍 3. Sumber Pencemar", 
    "🗺️ 4 & 5. Kerentanan & Zonasi Spasial", 
    "📉 6. Daya Tampung (DTBP)", 
    "📋 7. Rekomendasi & Kebijakan"
])

# ------------------------------------------
# TAB 1 & 2: STATUS MUTU & KELAYAKAN FUNGSI
# ------------------------------------------
with tabs[0]:
    st.header("Analisis Status Mutu dan Fungsi Peruntukan Air")
    st.write(f"**Lokasi Pengamatan:** {sample_name} (Kelurahan {kelurahan})")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Indeks Pencemaran (IP)", f"{ip_score:.3f}")
    col2.markdown(f"**Status Mutu Air:** <span style='color:{color_status}; font-size:20px; font-weight:bold;'>{status_mutu}</span>", unsafe_allow_html=True)
    col3.metric("Indeks Kualitas Air (IKA)", f"{ika_score} / 100")
    
    st.markdown("---")
    st.subheader("📋 Matriks Kelayakan Fungsi Peruntukan Air")
    
    # Logika Kelayakan Sektoral
    layak_minum = "LAYAK (Perlu Rebus/Filtrasi)" if (coliform < 50 and kesadahan < 500) else "TIDAK LAYAK (Kandungan Kapur/Bakteri Tinggi)"
    layak_irigasi = "LAYAK (Salinitas & Kimiawi Stabil)" if tds < 1000 else "TIDAK LAYAK (Risiko Salinisasi Tanah)"
    layak_perikanan = "LAYAK" if (6.5 <= ph <= 8.5 and cod < 25) else "TIDAK LAYAK (Resiko Defisit Oksigen/Fluktuasi pH)"
    
    df_kelayakan = pd.DataFrame({
        "Sektor Peruntukan": ["Air Minum & Domestik", "Pertanian & Irigasi", "Perikanan & Peternakan"],
        "Status Kelayakan": [layak_minum, list_irigasi := layak_irigasi, layak_perikanan],
        "Parameter Pembatas Utama": [
            "Total Coliform & Kesadahan Karst" if layak_minum != "LAYAK" else "Tidak ada",
            "TDS / Salinitas Batuan" if layak_irigasi != "LAYAK" else "Tidak ada",
            "Kadar COD dan Derajat Keasaman" if layak_perikanan != "LAYAK" else "Tidak ada"
        ]
    })
    st.table(df_kelayakan)

# ------------------------------------------
# TAB 3: IDENTIFIKASI SUMBER PENCEMAR
# ------------------------------------------
with tabs[1]:
    st.header("Fingerprinting & Identifikasi Sumber Pencemar")
    st.write("Sistem mendeteksi fluktuasi klaster parameter dominan untuk melacak asal polutan:")
    
    pencemaran_log = []
    if coliform > 10 or bod > 5:
        pencemaran_log.append("🚨 **Pencemaran Domestik Tinggi:** Indikasi rembesan limbah rumah tangga / *septic tank* padat penduduk akibat jarak sumur yang terlalu dekat.")
    if nitrat > 10:
        pencemaran_log.append("🚜 **Pencemaran Pertanian:** Terdeteksi akumulasi senyawa Nitrat ($NO_3$). Kemungkinan akibat limpasan pupuk atau kotoran ternak dari permukaan.")
    if kesadahan > 400 or tds > 500:
        pencemaran_log.append("🪨 **Karakteristik Latar Alami (Lithogenic):** Tingginya unsur Kalsium dan magnesium murni bersumber dari pelarutan batuan kapur Formasi Karst Alak.")
        
    if pencemaran_log:
        for log in pencemaran_log:
            st.markdown(log)
    else:
        st.success("Belum terdeteksi adanya anomali aktivitas antropogenik yang masif.")

# ------------------------------------------
# TAB 4 & 5: KERENTANAN & ZONASI SPASIAL
# ------------------------------------------
with tabs[2]:
    st.header("Pemetaan Kerentanan Air Tanah & Zonasi Ruang Permukaan")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("🛡️ Kerentanan Bawah Permukaan (Metode Karst-DRASTIC)")
        st.markdown(f"Status Kerentanan: <span style='color:{color_vun}; font-size:18px; font-weight:bold;'>{kerentanan_status}</span>", unsafe_allow_html=True)
        st.write(f"**Waktu Respons Perjalanan Polutan (Travel Time):** {travel_time}")
        st.info("Kawasan karst memiliki pori sekunder (rekahan gua) yang bertindak sebagai jalur pintas polutan (*contaminant shortcuts*) tanpa filtrasi tanah alami.")
        
    with col_g2:
        st.subheader("🗺️ Matriks Arahan Pemanfaatan Lahan (Zonasi)")
        if jarak_ponor < 100:
            st.error("**ZONA LINDUNG MUTLAK (ZONA INTI KONSERVASI)**\nDilarang mendirikan bangunan, tangki septik baru, kawasan industri, ataupun aktivitas penambangan batu kapur dalam radius ini.")
        else:
            st.warning("**ZONA BUDIDAYA TERBATAS**\nAktivitas pembangunan harus memiliki pengolahan limbah kedap air tingkat lanjut (STP) untuk menghindari kebocoran akuifer.")

# ------------------------------------------
# TAB 6: PEMODELAN DAYA TAMPUNG (DTBP)
# ------------------------------------------
with tabs[3]:
    st.header("Pemodelan Daya Tampung Beban Pencemaran (DTBP)")
    st.write("Analisis kuantitatif batas maksimal asimilasi polutan pada badan air penerima:")
    
    # Simulasi perhitungan DTBP sederhana untuk parameter BOD
    beban_aktual = (bod * 1500) / 1000 # simulasi debit 1500 m3/hari
    beban_maksimal = (5.0 * 1500) / 1000 # Baku mutu BOD kelas 2 = 5 mg/L
    dtbp_sisa = beban_maksimal - beban_aktual
    
    col_d1, col_d2 = st.columns(2)
    col_d1.metric("Beban Polutan Aktual Saat Ini", f"{beban_aktual:.2f} kg BOD/Hari")
    
    if dtbp_sisa > 0:
        col_d2.metric("Sisa Alokasi Alokasi Beban yang Diizinkan", f"{dtbp_sisa:.2f} kg BOD/Hari", delta="Aman")
        st.success("Badan air masih memiliki kapasitas asimilasi alami untuk menerima buangan limbah terkontrol.")
    else:
        col_d2.metric("Alokasi Beban Melebihi Batas (Defisit)", f"{dtbp_sisa:.2f} kg BOD/Hari", delta="Kritis", delta_color="inverse")
        st.error("**Daya Tampung Terlampaui!** Pemerintah daerah harus melakukan moratorium izin pembuangan limbah cair baru di sub-daerah aliran air ini.")

# ------------------------------------------
# TAB 7: REKOMENDASI TEKNIS & KEBIJAKAN
# ------------------------------------------
with tabs[4]:
    st.header("📋 Ultimate Output: Rekomendasi Teknis, Pengelolaan, & Kebijakan")
    
    st.subheader("🔧 1. Desain Teknologi Sistem Pengolahan Air (Water Treatment)")
    rekomendasi_teknis = []
    if kesadahan > 500:
        rekomendasi_teknis.append("* **Unit Penurun Kesadahan (Water Softener):** Memasang tabung penukar ion (*Ion Exchange Resin Kation*) untuk mengikat kandungan kapur ($Ca^{2+}$ dan $Mg^{2+}$) agar tidak memicu pembentukan kerak batu.")
    if coliform > 0:
        rekomendasi_teknis.append("* **Sistem Disinfeksi Sinar UV / Klorinasi Otomatis:** Untuk mensterilkan air dari paparan bakteri Coliform sebelum dialirkan ke jaringan distribusi rumah tangga.")
    if tds > 500:
        rekomendasi_teknis.append("* **Sistem Filtrasi Multi-Stage:** Pemasangan filter sedimen makro yang dipadukan dengan karbon aktif guna memperbaiki parameter estetika air (rasa dan bau).")
        
    if rekomendasi_teknis:
        for rek in rekomendasi_teknis:
            st.write(rek)
    else:
        st.write("* Air berada dalam kondisi prima alami. Cukup filtrasi sedimen standar.")
        
    st.markdown("---")
    st.subheader("🏛️ 2. Dokumen Naskah Rekomendasi Regulasi Tata Ruang (BAPPEDA/DLH)")
    
    # Teks Otomatisasi Draft Legalitas
    st.write(f"Berdasarkan analisis terintegrasi GeoWater-IQ pada lokasi **{sample_name}**, dirumuskan draf kebijakan sebagai berikut:")
    naskah_draft = f"""
    > **SURAT REKOMENDASI ILMIAH PENGELOLAAN HIDRO-KARST KOTA KUPANG**
    > 
    > 1. Menetapkan wilayah kelurahan **{kelurahan}** yang masuk ke dalam radius kerentanan radikal koridor gua/ponor sebagai **Kawasan Strategis Perlindungan Air Tanah**.
    > 2. Menginstruksikan pembuatan **Jaringan Sumur Pantau (Groundwater Monitoring Network)** di area hulu (*up-gradient*) dan hilir (*down-gradient*) dari Kecamatan Alak untuk sistem peringatan dini polutan transmisi kilat.
    > 3. Mewajibkan peninjauan ulang draf Rencana Tata Ruang Wilayah (RTRW) guna membatasi aktivitas ekstraktif industri masif gamping pada sub-zonasi yang memiliki skor kerentanan tinggi.
    """
    st.markdown(naskah_draft)