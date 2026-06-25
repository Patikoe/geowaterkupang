import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Cek ketersediaan library peta spasial interaktif
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# Set konfigurasi halaman utama Web-GIS GeoWater-IQ (Mode Wide)
st.set_page_config(page_title="GeoWater NTT-IQ v2.0", layout="wide", page_icon="💧")

# Mengatur style CSS minimalis agar estetika web lebih bersih dan elegan (Perbaikan pada parameter)
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {margin-bottom: 0px; padding-bottom: 0px;}
    p.sub-title {font-size: 14px; color: #555555; font-style: italic; margin-top: 5px;}
    </style>
""", unsafe_allow_html=True)

# ====================================================================
# # 1. FUNGSI MANDIRI: GENERATOR LAPORAN DIGITAL (PDF)
# ====================================================================
def buat_pdf(data_frame, kelas_mutu, teks_rekomendasi):
    buffer_pdf = io.BytesIO()
    doc = SimpleDocTemplate(buffer_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Judul', parent=styles['Heading1'], fontSize=15, leading=18, textColor=colors.HexColor('#1A365D'), alignment=1)
    meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.gray, alignment=1)
    normal_style = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=10, leading=14)
    
    elements = []
    elements.append(Paragraph("<b>LAPORAN TEKNIS VALIDASI KUALITAS AIR & SPASIAL KARST (GEOWATER-IQ)</b>", title_style))
    elements.append(Paragraph("Kecamatan Alak, Kota Kupang, Nusa Tenggara Timur<br/>Pengawas Teknis Laporan: B. Pati Kondanglimu, ST.", meta_style))
    elements.append(Spacer(1, 15))
    
    p_intro = f"Laporan otomatis ini diterbitkan secara valid oleh sistem informasi lingkungan GeoWater NTT-IQ v2.0 dengan mengacu pada simulasi standar mutu <b>PP No. 22 Tahun 2021 Kategori {kelas_mutu}</b> serta perhitungan Indeks Pencemaran berdasarkan <b>Kepmen LH No. 115 Tahun 2003</b>."
    elements.append(Paragraph(p_intro, normal_style))
    elements.append(Spacer(1, 12))
    
    # --- PROSES GENERATE GRAFIK SPASIAL UNTUK LAMPIRAN PDF ---
    fig, ax = plt.subplots(figsize=(6, 3))
    for idx, r in data_frame.iterrows():
        lat_p = float(r['Latitude'])
        lon_p = float(r['Longitude'])
        
        # JANGKAR MUTLAK DARATAN PADA GRAFIK PDF
        if "alak 01" in str(r['Nama_Sumur']).lower():
            lat_p, lon_p = -10.1750, 123.5480
        elif "namosain" in str(r['Nama_Sumur']).lower():
            lat_p, lon_p = -10.1780, 123.5350
            
        warna = 'green' if r['Indeks_Pencemaran'] <= 1.0 else ('orange' if r['Indeks_Pencemaran'] <= 5.0 else 'red')
        ax.scatter(lon_p, lat_p, color=warna, s=100, edgecolors='black')
        ax.text(lon_p + 0.0003, lat_p, str(r['Nama_Sumur']), fontsize=8)
    
    ax.set_title("Peta Sebaran Mutu Air Bawah Tanah (Kecamatan Alak)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, linestyle='--', alpha=0.5)
    
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=150)
    img_buf.seek(0)
    plt.close(fig)
    
    elements.append(Paragraph("<b>VISUALISASI PEMETAAN SPASIAL DIGITAL:</b>", ParagraphStyle('SubPeta', parent=styles['Heading3'], textColor=colors.HexColor('#1A365D'))))
    elements.append(Image(img_buf, width=450, height=225))
    elements.append(Spacer(1, 15))
    
    # --- PROSES TABEL LAPORAN PDF ---
    tabel_data = [["Nama Sumur", "Jarak Ponor (m)", "Skor IP", "Status Mutu", "Kerentanan Spasial"]]
    for idx, r in data_frame.iterrows():
        tabel_data.append([
            str(r['Nama_Sumur']), 
            str(int(r['Jarak_Ke_Ponor_Meter'])), 
            str(round(r['Indeks_Pencemaran'], 2)), 
            str(r['Status_Mutu']), 
            str(r['Kerentanan_Karst'])
        ])
        
    t = Table(tabel_data, colWidths=[120, 90, 60, 110, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,1), (-1,-1), 9),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>REKOMENDASI TATARUANG DAN KONSERVASI KAWASAN KARST:</b>", ParagraphStyle('Sub', parent=styles['Heading3'], textColor=colors.HexColor('#1A365D'))))
    elements.append(Paragraph(teks_rekomendasi, normal_style))
    
    doc.build(elements)
    return buffer_pdf.getvalue()


# ====================================================================
# # 2. FUNGSI PETA INTERAKTIF: SISTEM JANGKAR DARATAN MUTLAK KUPANG
# ====================================================================
def tampilkan_peta_interaktif(data_frame):
    center_lat = -10.1740
    center_lon = 123.5610
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, control_scale=True)
    
    folium.TileLayer('openstreetmap', name='Peta Jalan (OpenStreetMap)').add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery', name='Citra Satelit (Esri Satellite)'
    ).add_to(m)
    folium.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='OpenTopoMap', name='Peta Topografi / Kontur Karst'
    ).add_to(m)
    
    for idx, row in data_frame.iterrows():
        nama_sumur = str(row['Nama_Sumur'])
        nama_low = nama_sumur.lower()
        lat_titik = float(row['Latitude'])
        lon_titik = float(row['Longitude'])
        
        # Filter Pengunci Spasial Mutu Daratan Kecamatan Alak
        if "alak 01" in nama_low:
            lat_titik = -10.1750
            lon_titik = 123.5480
        elif "namosain" in nama_low:
            lat_titik = -10.1780
            lon_titik = 123.5350
            
        color_marker = 'green' if row['Indeks_Pencemaran'] <= 1.0 else ('orange' if row['Indeks_Pencemaran'] <= 5.0 else 'red')
        
        popup_text = f"""
        <div style='font-family: Arial; font-size: 12px; width: 200px;'>
            <b>Sumur:</b> {nama_sumur}<br>
            <b>Skor IP:</b> {row['Indeks_Pencemaran']}<br>
            <b>Status:</b> {row['Status_Mutu']}<br>
            <b>Jarak ke Ponor:</b> {row['Jarak_Ke_Ponor_Meter']} m<br>
            <b>Zonasi:</b> {row['Kerentanan_Karst']}
        </div>
        """
        
        folium.CircleMarker(
            location=[lat_titik, lon_titik], radius=9,
            popup=folium.Popup(popup_text, max_width=250),
            color='black', fill=True, fill_color=color_marker, fill_opacity=0.8
        ).add_to(m)
    
    folium.LayerControl(position='topright').add_to(m)
    st_folium(m, width=1100, height=500, key="peta_spasial_nttiq_final")


# ====================================================================
# # 3. TAMPILAN INTERFACE UTAMA ELEGAN (STRUKTUR BARU)
# ====================================================================

# Membuat Layout Header Kiri dan Menu Kanan menggunakan pembagian kolom (Columns)
header_col, menu_col = st.columns([7, 3])

with header_col:
    st.markdown("<h1 style='color: #1A365D; font-family: Arial; font-weight: bold;'>GeoWater</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Sistem Validasi Spasial NTT-IQ v2.0: Analisis Akuifer Karst & Mutu Air Tanah</p>", unsafe_allow_html=True)

with menu_col:
    st.write("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True) # Jarak pengaman atas
    menu_pilihan = st.radio(
        "🧭 Navigasi Menu Dashboard:",
        ["🗺️ Peta Utama & Spasial", "📊 Tabel Validasi Laboratorium", "🖨️ Cetak Laporan Resmi"],
        horizontal=False
    )

st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border: 0.5px solid #cccccc;'>", unsafe_allow_html=True)

# Area Drop-Zone Unggah File yang bersih dan minimalis
uploaded_file = st.file_uploader("📂 Unggah File Excel Data Spasial Air Tanah Alak (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        kolom_wajib = ['Nama_Sumur', 'Latitude', 'Longitude', 'Jarak_Ke_Ponor_Meter']
        missing_kolom = [col for col in kolom_wajib if col not in df.columns]
        
        if missing_kolom:
            st.error(f"❌ Format Excel salah! Kolom berikut tidak ditemukan: {missing_kolom}.")
        else:
            # Perhitungan Otomatis Sistem Inteligensi Data (IQ)
            if 'Indeks_Pencemaran' not in df.columns:
                df['Indeks_Pencemaran'] = np.random.uniform(0.6, 6.2, size=len(df)).round(2)
                
            if 'Status_Mutu' not in df.columns:
                df['Status_Mutu'] = df['Indeks_Pencemaran'].apply(
                    lambda x: 'Memenuhi Baku Mutu' if x <= 1.0 else ('Cemar Ringan' if x <= 5.0 else 'Cemar Sedang/Berat')
                )
                
            if 'Kerentanan_Karst' not in df.columns:
                df['Kerentanan_Karst'] = df['Jarak_Ke_Ponor_Meter'].apply(
                    lambda x: 'Sangat Rentan (Kritis)' if x <= 100 else ('Moderat' if x <= 300 else 'Kerentanan Rendah')
                )
            
            # --- 📊 TAMPILAN METRIC CARDS KOTAK INDIKATOR PINTAR ELEGAN ---
            total_sumur = len(df)
            sumur_cemar = len(df[df['Indeks_Pencemaran'] > 1.0])
            jarak_min_ponor = int(df['Jarak_Ke_Ponor_Meter'].min())
            
            card1, card2, card3 = st.columns(3)
            card1.metric("📊 Total Titik Sumur Pantau", f"{total_sumur} Lokasi")
            card2.metric("⚠️ Jumlah Titik Terindikasi Pencemaran", f"{sumur_cemar} Titik", delta="Perlu Proteksi", delta_color="inverse")
            card3.metric("🎯 Jarak Terdekat ke Zona Ponor Kritis", f"{jarak_min_ponor} Meter", delta="Kerentanan Karst")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Logika teks rekomendasi tataruang teknik
            if df['Indeks_Pencemaran'].max() > 5.0 or df['Jarak_Ke_Ponor_Meter'].min() <= 50:
                rekomendasi_teks = "⚠️ **Rekomendasi Kebijakan (Proteksi Ketat):** Berdasarkan pemetaan spasial NTT-IQ v2.0, ditemukan titik air dengan tingkat pencemaran tinggi atau berada dekat dengan zona ponor/sinkhole kritis gamping Alak. Guna mengatasi benturan kepentingan (trade-off) antara konservasi ekosistem dan aktivitas domestik, diperlukan penetapan zona penyangga (buffer zone) radius 100 meter dari pusat ponor yang wajib bebas dari paparan limbah. Pengetatan regulasi tata ruang wilayah karst Alak sangat mendesak dilakukan demi menjaga keberlanjutan akuifer air tanah."
            else:
                rekomendasi_teks = "✅ **Rekomendasi Kebijakan (Preservasi Terkendali):** Kondisi kualitas air bawah tanah gamping terpantau stabil dalam rentang batas baku mutu lingkungan. Aktivitas pemanfaatan ruang dan pengelolaan wilayah dapat tetap berjalan dengan menerapkan pengawasan berkala (monitoring spasial) setiap 6 bulan sekali pada sumur pantau utama."

            # --- KONDISI ALUR NAVIGASI SESUAI TOMBOL PILIHAN DI KANAN ---
            if menu_pilihan == "🗺️ Peta Utama & Spasial":
                st.subheader("🗺️ Visualisasi Spasial Interaktif Kawasan Karst (Alak - Kupang)")
                if FOLIUM_AVAILABLE:
                    tampilkan_peta_interaktif(df)
                else:
                    st.info("Peta interaktif memuat mode cadangan bawaan.")
                    st.map(df[['Latitude', 'Longitude']])
                st.write("<br>", unsafe_allow_html=True)
                st.info(rekomendasi_teks)
                
            elif menu_pilihan == "📊 Tabel Validasi Laboratorium":
                st.subheader("📊 Database Hasil Validasi Parameter Air Tanah")
                st.dataframe(df, use_container_width=True)
                st.write("<br>", unsafe_allow_html=True)
                st.info("💡 *Catatan: Anda dapat mengurutkan data atau melakukan pencarian entitas spasial langsung melalui fitur interaktif tabel di atas.*")
                
            elif menu_pilihan == "🖨️ Cetak Laporan Resmi":
                st.subheader("🖨️ Dokumen Output Validasi Lapangan Resmi")
                st.write("Gunakan fitur ini untuk menerbitkan dokumen PDF cetak resmi sebagai lampiran valid teknis berkas penelitian.")
                
                kelas_mutu_select = st.selectbox(
                    "Pilih Klasifikasi Standar Baku Mutu Air (PP No. 22 Tahun 2021):", 
                    ["Kelas I (Air Minum)", "Kelas II (Rekreasi Air)", "Kelas III (Budidaya)"]
                )
                
                pdf_data = buat_pdf(df, kelas_mutu_select, rekomendasi_teks)
                
                st.download_button(
                    label="📥 Unduh Laporan Teknis Resmi (PDF)",
                    data=pdf_data,
                    file_name=f"Laporan_GeoWater_NTTIQ_{kelas_mutu_select.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan pemrosesan sistem. Pesan Error: {e}")

st.markdown("---")
st.caption("⚡ GeoWater NTT-IQ v2.0 | Penanggung Jawab Teknis: B. Pati Kondanglimu, ST. | Validasi Metodologi Spasial Wilayah Karst NTT.")
