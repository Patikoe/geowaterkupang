import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. KONFIGURASI HALAMAN UTAMA
st.set_page_config(page_title="GeoWater-IQ Web-GIS", layout="wide", page_icon="💧")

st.title("💧 GeoWater-IQ v2.0 (Sistem Web-GIS Terintegrasi)")
st.subheader("Analisis Kualitas Air, Kerentanan Karst, & Rekomendasi Tata Ruang Kecamatan Alak, Kota Kupang")
st.write("Sistem Pemantauan Lingkungan Digital — Pengawasan Teknis: B. Pati Kondanglimu, ST.")

# 2. DATABASE BAKU MUTU REGIONAL (PP No. 22 Tahun 2021)
BAKU_MUTU = {
    "Kelas 1 (Air Minum/Domestik)": {"pH_min": 6.0, "pH_max": 9.0, "BOD": 2.0, "COD": 10.0, "DO_min": 6.0, "Nitrat": 10.0, "Kesadahan": 500.0},
    "Kelas 2 (Prasarana Rekreasi Air)": {"pH_min": 6.0, "pH_max": 9.0, "BOD": 3.0, "COD": 25.0, "DO_min": 4.0, "Nitrat": 10.0, "Kesadahan": 800.0},
    "Kelas 3 (Budidaya Ikan & Peternakan)": {"pH_min": 6.0, "pH_max": 9.0, "BOD": 6.0, "COD": 40.0, "DO_min": 3.0, "Nitrat": 20.0, "Kesadahan": 1000.0},
    "Kelas 4 (Irigasi Pertanian Gamping)": {"pH_min": 6.0, "pH_max": 9.0, "BOD": 12.0, "COD": 80.0, "DO_min": 0.0, "Nitrat": 20.0, "Kesadahan": 1200.0}
}

# 3. FUNGSI LOGIKA HITUNG INDEKS PENCEMARAN (Kepmen LH 115/2003)
def hitung_ip(row, kriteria):
    sub_indices = []
    if row['pH'] < kriteria['pH_min']:
        sub_indices.append((kriteria['pH_min'] - row['pH']) / (kriteria['pH_min'] - 4.0))
    elif row['pH'] > kriteria['pH_max']:
        sub_indices.append((row['pH'] - kriteria['pH_max']) / (14.0 - kriteria['pH_max']))
    else:
        sub_indices.append(0.0)
        
    for param in ['BOD', 'COD', 'Nitrat', 'Kesadahan']:
        sub_indices.append(row[param] / kriteria[param])
        
    if row['DO'] >= kriteria['DO_min']:
        sub_indices.append(0.0)
    else:
        sub_indices.append((kriteria['DO_min'] - row['DO']) / kriteria['DO_min'])
        
    n_max = np.max(sub_indices)
    n_rerata = np.mean(sub_indices)
    
    ip = np.sqrt((n_max**2 + n_rerata**2) / 2)
    return round(ip, 2)

def evaluasi_status(ip):
    if ip <= 1.0: return "Memenuhi Baku Mutu", "🟢"
    elif ip <= 5.0: return "Cemar Ringan", "🟡"
    elif ip <= 10.0: return "Cemar Sedang", "🟠"
    else: return "Cemar Berat", "🔴"

# 4. SIDEBAR PANEL CONTROL
st.sidebar.header("🛠️ Panel Kendali Sistem")
pilihan_kelas = st.sidebar.selectbox("Pilih Kategori Peruntukan Air (PP 22/2021):", list(BAKU_MUTU.keys()))
kriteria_terpilih = BAKU_MUTU[pilihan_kelas]

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Fitur 1: Unggah Data Batch (Excel)")
uploaded_file = st.sidebar.file_uploader("Unggah Tabel Sampel Lapangan (.xlsx)", type=["xlsx"])

template_data = {
    'Nama_Sumur': ['Sumur Warga Alak 01', 'Sumur Pantau 02'],
    'Latitude': [-10.1650, -10.1720],
    'Longitude': [123.5520, 123.5480],
    'Jarak_Ke_Ponor_Meter': [120, 45],
    'pH': [7.2, 6.8],
    'BOD': [1.5, 3.2],
    'COD': [8.0, 28.0],
    'DO': [6.2, 4.1],
    'Nitrat': [4.5, 12.1],
    'Kesadahan': [320.0, 550.0]
}
df_template = pd.DataFrame(template_data)
output_template = io.BytesIO()
with pd.ExcelWriter(output_template, engine='openpyxl') as writer:
    df_template.to_excel(writer, index=False, sheet_name='Sheet1')
st.sidebar.download_button(label="📁 Unduh Template Excel Lapangan", data=output_template.getvalue(), file_name="template_geowater_alak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# 5. PEMROSESAN UTAMA APLIKASI
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        df['Indeks_Pencemaran'] = df.apply(lambda r: hitung_ip(r, kriteria_terpilih), axis=1)
        df['Status_Mutu'] = df['Indeks_Pencemaran'].apply(lambda x: evaluasi_status(x)[0])
        df['Penanda_Warna'] = df['Indeks_Pencemaran'].apply(lambda x: evaluasi_status(x)[1])
        
        def nilai_kerentanan(jarak):
            if jarak <= 50: return "Sangat Tinggi (Zona Kritis Karst)", "🔴"
            elif jarak <= 150: return "Sedang-Tinggi", "🟠"
            else: return "Relatif Aman/Rendah", "🟢"
        df['Kerentanan_Karst'] = df['Jarak_Ke_Ponor_Meter'].apply(lambda x: nilai_kerentanan(x)[0])

        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("📊 Hasil Pemrosesan Logika Kimia Air & Kerentanan Spasial")
            st.dataframe(df[['Nama_Sumur', 'Jarak_Ke_Ponor_Meter', 'Indeks_Pencemaran', 'Status_Mutu', 'Kerentanan_Karst']])
            
        with col2:
            st.subheader("📉 Ringkasan Kondisi Lapangan")
            total_titik = len(df)
            cemar_total = len(df[df['Indeks_Pencemaran'] > 1.0])
            st.metric("Total Sampel Sumur Dipantau", f"{total_titik} Titik")
            st.metric("Titik Terindikasi Melebihi Baku Mutu", f"{cemar_total} Titik", delta=f"{round((cemar_total/total_titik)*100, 1)}% Risiko", delta_color="inverse")

        st.markdown("---")
        
        # 6. FITUR 2: INTEGRASI PEMETAAN INTERAKTIF (WEB-GIS INTERAKTIF)
        st.subheader("🗺️ Visualisasi Sistem Informasi Geografis (Web-GIS) Kecamatan Alak")
        st.write("Peta interaktif di bawah mendeteksi koordinat riil dan menunjukkan zonasi kerentanan air berdasarkan penanda spasial.")
        
        map_center = [df['Latitude'].mean(), df['Longitude'].mean()]
        m = folium.Map(location=map_center, zoom_start=14, control_scale=True)
        
        # Menggunakan Citra Satelit Google Resmi
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Menambahkan Opsi Google Hybrid (Satelit + Nama Jalan)
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Hybrid (Satelit + Jalan)',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer('openstreetmap', name='Peta Jalan Standar').add_to(m)
        folium.LayerControl().add_to(m)

        for _, row in df.iterrows():
            warna_map = 'green' if row['Indeks_Pencemaran'] <= 1.0 else ('orange' if row['Indeks_Pencemaran'] <= 5.0 else 'red')
            popup_text = f"""
            <div style='font-family: Arial, sans-serif; width: 220px;'>
                <b>📌 {row['Nama_Sumur']}</b><br>
                <hr style='margin: 4px 0;'>
                <b>Indeks Pencemaran:</b> {row['Indeks_Pencemaran']}<br>
                <b>Status Mutu:</b> {row['Status_Mutu']}<br>
                <b>Kerentanan Karst:</b> {row['Kerentanan_Karst']}<br>
                <b>Jarak ke Ponor:</b> {row['Jarak_Ke_Ponor_Meter']} meter
            </div>
            """
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(popup_text, max_width=250),
                icon=folium.Icon(color=warna_map, icon='info-sign')
            ).add_to(m)
            
        st_folium(m, width=1100, height=500)

        st.markdown("---")
        
        # 7. REKOMENDASI TATA RUANG OTOMATIS BERDASARKAN HASIL DATA
        st.subheader("📋 Rekomendasi Kebijakan Tata Ruang & Konservasi Kawasan")
        rekomendasi_teks = ""
        if df['Indeks_Pencemaran'].max() > 5.0 or df['Jarak_Ke_Ponor_Meter'].min() <= 50:
            rekomendasi_teks = "⚠️ **Rekomendasi Utama (Proteksi Ketat):** Ditemukan titik air dengan tingkat pencemaran tinggi atau berada dekat struktur ponor/sinkhole kritis gamping Alak. Diperlukan penetapan zona penyangga (buffer zone) radius 100m dari ponor bebas dari aktivitas pembuangan limbah domestik maupun industri pertambangan. Pengetatan perizinan tata ruang wilayah karst Alak sangat mendesak dilakukan."
        else:
            rekomendasi_teks = "✅ **Rekomendasi Utama (Preservasi Terkendali):** Kondisi kualitas air bawah tanah gamping terpantau stabil dalam rentang baku mutu peruntukan. Aktivitas tata ruang dapat dilanjutkan dengan skema pemantauan berkala setiap 6 bulan guna mendeteksi intrusi air laut atau rembesan kontaminan dini."
        st.info(rekomendasi_teks)

        # 8. FITUR 3: GENERATOR LAPORAN DIGITAL (PDF)
        st.subheader("🖨️ Cetak Dokumen Output Hasil Validasi Lapangan")
def buat_pdf(data_frame, kelas_mutu, teks_rekomendasi):
    # --- 1. BLOK IMPOR LENGKAP DAN VALID ---
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.platypus.tables import Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    import io
    
    buffer_pdf = io.BytesIO()
    doc = SimpleDocTemplate(buffer_pdf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Judul', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#1A365D'), alignment=1)
    meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.gray, alignment=1)
    normal_style = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=10, leading=14)
    
    elements = []
    elements.append(Paragraph("<b>LAPORAN TEKNIS VALIDASI KUALITAS AIR & SPASIAL KARST (GEOWATER-IQ)</b>", title_style))
    elements.append(Paragraph("Kecamatan Alak, Kota Kupang, Nusa Tenggara Timur<br/>Pengawas Teknis Pembuat Aplikasi: B. Pati Kondanglimu, ST.", meta_style))
    elements.append(Spacer(1, 15))
    
    p_intro = f"Laporan otomatis ini diterbitkan secara valid oleh sistem informasi lingkungan GeoWater-IQ v2.0 dengan mengacu pada simulasi standar mutu <b>PP No. 22 Tahun 2021 Kategori {kelas_mutu}</b> serta perhitungan Indeks Pencemaran berdasarkan <b>Kepmen LH No. 115 Tahun 2003</b>."
    elements.append(Paragraph(p_intro, normal_style))
    elements.append(Spacer(1, 12))
    
    # --- 2. PROSES GENERATE PETA SPASIAL UNTUK PDF ---
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 3))
    
    for _, r in data_frame.iterrows():
        warna = 'green' if r['Indeks_Pencemaran'] <= 1.0 else ('orange' if r['Indeks_Pencemaran'] <= 5.0 else 'red')
        ax.scatter(r['Longitude'], r['Latitude'], color=warna, s=100, edgecolors='black', label=r['Status_Mutu'])
        ax.text(r['Longitude'] + 0.0005, r['Latitude'], r['Nama_Sumur'], fontsize=8)
    
    ax.set_title("Peta Sebaran Mutu Air Bawah Tanah (Kecamatan Alak)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, linestyle='--', alpha=0.5)
    
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=8)
    
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=150)
    img_buf.seek(0)
    plt.close(fig)
    
    elements.append(Paragraph("<b>VISUALISASI PEMETAAN SPASIAL DIGITAL:</b>", ParagraphStyle('SubPeta', parent=styles['Heading3'], textColor=colors.HexColor('#1A365D'))))
    elements.append(Image(img_buf, width=450, height=225))
    elements.append(Spacer(1, 15))
    
    # --- 3. PROSES STRUKTUR TABEL LAPORAN ---
    tabel_data = [["Nama Sumur", "Jarak Ponor (m)", "Skor IP", "Status Mutu", "Kerentanan Spasial"]]
    for _, r in data_frame.iterrows():
        tabel_data.append([r['Nama_Sumur'], str(r['Jarak_Ke_Ponor_Meter']), str(r['Indeks_Pencemaran']), r['Status_Mutu'], r['Kerentanan_Karst']])
        
    t = Table(tabel_data, colWidths=[130, 90, 60, 110, 130])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,1), (-1,-1), 9),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>REKOMENDASI TATARUANG DAN KONSERVASI:</b>", ParagraphStyle('Sub', parent=styles['Heading3'], textColor=colors.HexColor('#1A365D'))))
    elements.append(Paragraph(teks_rekomendasi, normal_style))
    
    doc.build(elements)
    return buffer_pdf.getvalue()
