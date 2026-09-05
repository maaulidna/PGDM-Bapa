import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Konfigurasi Halaman agar Responsif
st.set_page_config(
    page_title="Pemantauan Gula Darah Mandiri Sugiyo RH",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kustomisasi CSS untuk tampilan mobile yang nyaman
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# 2. Fungsi Mengambil Data dari Google Sheets
# Ganti SPREADSHEET_ID dengan ID dokumen Anda
SPREADSHEET_ID = "1e39QSZP1nk9aLUfU4hpg4XgWjk-UB7edbo5m_FQObn4"
SHEET_NAME = "Form%20Responses%201"

@st.cache_data(ttl=60)  # Refresh otomatis setiap 60 detik
def load_data():
    # URL ekspor CSV langsung dari Google Sheets (Pastikan akses sheet: 'Anyone with the link can view')
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    df = pd.read_csv(csv_url)
    
    # Konversi tanggal
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce', dayfirst=True)
    df['Gula Darah'] = pd.to_numeric(df['Gula Darah'], errors='coerce')
    df = df.dropna(subset=['Tanggal', 'Gula Darah'])
    df = df.sort_values(by=['Tanggal', 'Timestamp'])
    
    # Tambahkan kolom Minggu/Pekan
    df['Minggu'] = df['Tanggal'].dt.to_period('W').apply(lambda r: f"{r.start_time.strftime('%d/%m')} - {r.end_time.strftime('%d/%m')}")
    return df

try:
    data = load_data()
except Exception as e:
    st.error(f"Gagal mengambil data dari Google Sheets. Pastikan akses tautan sheet sudah diatur ke 'Siapa saja yang memiliki link'. Detail: {e}")
    st.stop()

# 3. Header
st.title("🩺 Pemantauan Gula Darah Mandiri Sugiyo RH")
st.caption("Pengobatan: oral + insulin")
st.caption("Dosis: 3x metformin 500 mg, 2x gliclazide 80mg, 1x insulin ryzodeg")

# 4. Filter di Sidebar
with st.sidebar:
    st.header("🔍 Filter Data")
    min_date = data['Tanggal'].min().date()
    max_date = data['Tanggal'].max().date()
    
    date_range = st.date_input("Pilih Rentang Tanggal:", [min_date, max_date])
    
    list_waktu = ["Semua"] + list(data['Waktu'].dropna().unique())
    selected_waktu = st.selectbox("Pilih Waktu Pemeriksaan:", list_waktu)

# Terapkan Filter
filtered_df = data.copy()
if len(date_range) == 2:
    start_d, end_d = date_range
    filtered_df = filtered_df[(filtered_df['Tanggal'].dt.date >= start_d) & (filtered_df['Tanggal'].dt.date <= end_d)]

if selected_waktu != "Semua":
    filtered_df = filtered_df[filtered_df['Waktu'] == selected_waktu]

# 5. Ringkasan Metrik (KPI)
st.markdown("### 📊 Ringkasan")
col1, col2, col3, col4 = st.columns(4)

# Hitung Rata-rata 7 Hari Terakhir
terakhir_tgl = data['Tanggal'].max()
seminggu_lalu = terakhir_tgl - pd.Timedelta(days=7)
avg_7_hari = data[data['Tanggal'] >= seminggu_lalu]['Gula Darah'].mean()

# Hitung Rata-rata Keseluruhan & Terkini
avg_total = data['Gula Darah'].mean()
last_record = data.iloc[-1]

with col1:
    st.metric("Rata-rata 7 Hari", f"{avg_7_hari:.1f} mg/dL" if pd.notnull(avg_7_hari) else "-")
with col2:
    st.metric("Rata-rata Total", f"{avg_total:.1f} mg/dL" if pd.notnull(avg_total) else "-")
with col3:
    st.metric("Pemeriksaan Terakhir", f"{last_record['Gula Darah']:.0f} mg/dL")
with col4:
    kategori = "Normal" if last_record['Gula Darah'] < 140 else ("Waspada" if last_record['Gula Darah'] <= 199 else "Tinggi")
    warna = "green" if kategori == "Normal" else ("orange" if kategori == "Waspada" else "red")
    st.markdown(f"**Status Terakhir:** <br><span style='color:{warna}; font-size: 20px; font-weight: bold;'>{kategori}</span>", unsafe_allow_html=True)

st.divider()

# 6. Tab Visualisasi & Data
tab_tren, tab_mingguan, tab_tabel = st.tabs(["📈 Tren Gula Darah", "📅 Rata-rata Mingguan", "📋 Tabel Riwayat"])

with tab_tren:
    st.subheader("Tren Kadar Gula Darah (Garis Berkelanjutan)")
    
    if not filtered_df.empty:
        # Urutkan data secara kronologis (berdasarkan tanggal dan waktu input)
        df_plot = filtered_df.sort_values(by=['Tanggal', 'Timestamp']).copy()
        
        # Buat label sumbu X yang informatif: Tanggal - Waktu Sesi
        df_plot['Label_Pemeriksaan'] = (
            df_plot['Tanggal'].dt.strftime('%d/%m/%Y') + " - " + df_plot['Waktu'].fillna('')
        )

        # 1. Buat grafik garis bersambung (Spline / Smooth Line)
        fig_tren = go.Figure()

        # Garis utama yang menyambungkan seluruh titik
        fig_tren.add_trace(go.Scatter(
            x=df_plot['Label_Pemeriksaan'],
            y=df_plot['Gula Darah'],
            mode='lines+markers',  # Garis menyambung + titik penanda
            line=dict(
                color='#2b7bba',    # Warna biru seperti di Google Sheets Anda
                width=3,
                shape='spline',     # 'spline' membuat garis melengkung halus / luwes
                smoothing=1.3
            ),
            marker=dict(
                size=9,
                symbol='star-diamond',  # Bentuk bintang/diamond seperti di Google Sheets
                color='#2b7bba',
                line=dict(width=1, color='white')
            ),
            name='Kadar Gula Darah',
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Kadar Gula: <b>%{y} mg/dL</b><br>" +
                "Menu: %{customdata[0]}<br>" +
                "Catatan: %{customdata[1]}<extra></extra>"
            ),
            customdata=df_plot[['Menu Makanan', 'Catatan']].fillna('-').values
        ))

        # 2. Garis batas target/waspada
        fig_tren.add_hline(
            y=180, 
            line_dash="dot", 
            line_color="#e67e22", 
            annotation_text="Batas Aman Setelah Makan (180 mg/dL)",
            annotation_position="top left"
        )
        fig_tren.add_hline(
            y=130, 
            line_dash="dot", 
            line_color="#27ae60", 
            annotation_text="Batas Sebelum Makan (130 mg/dL)",
            annotation_position="bottom left"
        )

        # 3. Kustomisasi Layout agar rapi di layar HP & Laptop
        fig_tren.update_layout(
            yaxis_title="Gula Darah (mg/dL)",
            xaxis_title="",
            hovermode="x unified",
            yaxis=dict(range=[0, max(df_plot['Gula Darah'].max() + 50, 250)]),
            xaxis=dict(tickangle=-45),  # Miringkan label tanggal agar terbaca jelas
            margin=dict(l=20, r=20, t=30, b=80),
            template="plotly_white"
        )

        st.plotly_chart(fig_tren, use_container_width=True)
    else:
        st.info("Tidak ada data pada filter yang dipilih.")

with tab_mingguan:
    st.subheader("Rata-rata Gula Darah per Pekan")
    
    # Pengelompokan data mingguan yang sudah diperbaiki
    df_weekly = (
        data.groupby('Minggu')['Gula Darah']
        .agg(['mean', 'count'])
        .reset_index()
    )
    df_weekly.columns = ['Pekan', 'Rata-rata', 'Jumlah Cek']
    
    if not df_weekly.empty:
        max_y = max(df_weekly['Rata-rata'].max() + 50, 250) if pd.notnull(df_weekly['Rata-rata'].max()) else 250
        
        fig_weekly = px.bar(
            df_weekly,
            x='Pekan',
            y='Rata-rata',
            text='Rata-rata',
            hover_data=['Jumlah Cek'],
            labels={'Rata-rata': 'Rata-rata (mg/dL)', 'Pekan': 'Rentang Tanggal'},
            color='Rata-rata',
            color_continuous_scale='Blues'
        )
        fig_weekly.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_weekly.update_layout(yaxis_range=[0, max_y])
        st.plotly_chart(fig_weekly, use_container_width=True)
    else:
        st.info("Belum ada data untuk rekap mingguan.")

with tab_tabel:
    st.subheader("Riwayat Detail Respon Form")
    kolom_tampil = ['Tanggal', 'Waktu', 'Gula Darah', 'Menu Makanan', 'Olahraga', 'Catatan']
    kolom_ada = [c for c in kolom_tampil if c in filtered_df.columns]
    st.dataframe(filtered_df[kolom_ada].sort_values(by='Tanggal', ascending=False), use_container_width=True)
