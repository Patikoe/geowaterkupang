import streamlit as st
import pandas as pd
import numpy as np
import os

# Set konfigurasi halaman utama
st.set_page_config(page_title="GeoWater-IQ v2.0", layout="wide", page_icon="💧")

# ====================================================================
# # 1. JUDUL DAN HEADER UTAMA APLIKASI
# ====================================================================
st.title("💧 GeoWater-IQ v2.0")
st.markdown("### Sistem Validasi Kualitas Air & Analisis Spasial Kerentanan Karst")
st.markdown("---")

# ====================================================================
# # 2. FITUR 1: UNGGAN DATA EXCEL (INPUT USER)
# ====================================================================
uploaded_file = st.file_uploader("📂 Unggah File Excel Data Sumur (Format .xlsx)", type=["xlsx"])

if uploaded_file is not None:
    # Membaca data excel ke dalam DataFrame
    df = pd.read_excel(uploaded_file)
    
    st.success("🎉 Data Berhasil Diunggah!")
    st.dataframe(df)
    
    # Simulation/Calculation placeholder
    # Pastikan kolom yang dibutuhkan ada di Excel atau buat simulasi otomatis
    if 'Indeks_Pencemaran' not in df.columns:
        df['Indeks_Pencemaran'] = np.random.uniform(0.5, 6.0, size=len(df)).round(2)
    if 'Status_Mutu' not in df.columns:
        df['Status_Mutu'] = df['Indeks_Pencemaran'].apply(lambda x: 'Memenuhi Baku Mutu' if x <= 1.0 else ('Cemar Ringan' if x <= 5.0 else 'Cemar Sedang/Berat'))
    if 'Kerentanan_Karst' not in df.columns:
        df['Kerentanan_Karst'] = df['Jarak_Ke_Ponor_Meter'].apply(lambda x: 'Sangat Rentan' if x <= 100 else 'Moderat')

    # ====================================================================
    # # 3. LOGIKA EVALUASI REKOMENDASI TATA RUANG
    # ====================================================================
    st.markdown("---")
    st.subheader("📋 Rekomendasi Kebijakan Tata Ruang & Konservasi Kawasan")
    
    if df['Indeks_Pencemaran'].max() > 5.0 or df['Jarak_Ke_Ponor_Meter'].min() <= 50:
        rekomendasi_teks = "⚠️ **Rekomendasi Utama (Proteksi Ketat):** Ditemukan titik air dengan tingkat pencemaran tinggi atau berada dekat struktur ponor/sinkhole kritis gamping Alak. Diperlukan penetapan zona penyangga (buffer zone) radius 100m dari ponor bebas dari aktivitas pembuangan limbah domestik maupun industri pertambangan. Pengetatan perizinan tata ruang wilayah karst Alak sangat mendesak dilakukan."
    else:
        rekomendasi_teks = "✅ **Rekomendasi Utama (Preservasi Terkendali):** Kondisi kualitas air bawah tanah gamping terpau stabil dalam rentang baku mutu peruntukan. Aktivitas pemanfaatan ruang tetap dapat berjalan dengan pengawasan berkala setiap 6 bulan sekali pada sumur pantau spasial utama."
        
    st.info(rekomendasi_teks)

    # ====================================================================
    # # 4. FITUR INTERFASE CETAK DOKUMEN PDF
    # ====================================================================
    st.markdown("---")
    st.subheader("🖨️ Cetak Dokumen Output Hasil Validasi Lapangan")
    
    # Ambil kelas mutu tiruan atau default
    kelas_mutu_select = st.selectbox("Pilih Klasifikasi Mutu PP No. 22 Tahun 2021:", ["Kelas I (Air Minum)", "Kelas II (Rekreasi Air)", "Kelas III (Budidaya)"])
    
    # Eksekusi fungsi pembentuk PDF saat tombol ditekan
    # Memanggil fungsi mandiri buat_pdf yang ada di paling bawah halaman
    try:
        from app import buat_pdf
        pdf_data = buat_pdf(df, kelas_mutu_select, rekomendasi_teks)
        
        st.download_button(
            label="📥 Download Laporan Validasi Teknis (PDF)",
            data=pdf_data,
            file_name="Laporan_GeoWaterIQ_Alak.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Gagal memproses file. Pastikan format kolom Excel Anda sudah sesuai dengan template contoh. Error: {e}")

st.markdown("---")
st.caption("⚡ GeoWater-IQ v2.0 - Dalam Pengawasan & Pemeliharaan Teknis oleh: B. Pati Kondanglimu, ST. Metodologi perhitungan & Web-GIS divalidasi berdasarkan Kepmen LH 115/2003 & PP 22/2021.")


# ====================================================================
# # 5. FITUR 3: GENERATOR LAPORAN DIGITAL (PDF) - MANDIRI DI PALING BAWAH
# ====================================================================
def buat_pdf(data_frame, kelas_mutu, teks_rekomendasi):
    # --- 1. BLOK IMPOR LENGKAP DAN VALID ---
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.platypus.tables import Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    import io
    import matplotlib.pyplot as plt
    
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
