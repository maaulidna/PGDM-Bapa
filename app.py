import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# 1. Konfigurasi Halaman (WAJIB di paling atas)
st.set_page_config(
    page_title="Pemantauan Gula Darah Mandiri Sugiyo RH",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Pemetaan Waktu ke Inisial Huruf Alfabetis (A - G)
MAPPING_WAKTU = {
    'Sebelum Makan Pagi': 'A',
    'Setelah Makan Pagi': 'B',
    'Sebelum Makan Siang': 'C',
    'Setelah Makan Siang': 'D',
    'Sebelum Makan Malam': 'E',
    'Setelah Makan Malam': 'F',
    'Sebelum Tidur Malam': 'G'
}

# 2. Fungsi Mengambil Data dari Google Sheets
SPREADSHEET_ID = "1e39QSZP1nk9aLUfU4hpg4XgWjk-UB7edbo5m_FQObn4"
SHEET_NAME = "Form%20Responses%201"

@st.cache_data(ttl=60)
def load_data():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    df = pd.read_csv(csv_url)

    df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce', dayfirst=True)
    df['Gula Darah'] = pd.to_numeric(df['Gula Darah'], errors='coerce')
    df = df.dropna(subset=['Tanggal', 'Gula Darah'])

    df['Waktu_Bersih'] = df['Waktu'].astype(str).str.strip()
    df['waktu_kode'] = df['Waktu_Bersih'].map(MAPPING_WAKTU).fillna('Z')
    df = df.sort_values(by=['Tanggal', 'waktu_kode'])

    df['Minggu'] = df['Tanggal'].dt.to_period('W').apply(
        lambda r: f"{r.start_time.strftime('%d/%m')} - {r.end_time.strftime('%d/%m')}"
    )
    return df

try:
    data = load_data()
except Exception as e:
    st.error(f"Gagal mengambil data dari Google Sheets: {e}")
    st.stop()

# -------------------------------------------------------------
# FUNGSI MEMBUAT TEMPLATE LAPORAN A4 CETAK
# -------------------------------------------------------------
def generate_print_html(df_filtered, full_data, date_str):
    # Hitung metrik
    terakhir_tgl = full_data['Tanggal'].max()
    seminggu_lalu = terakhir_tgl - pd.Timedelta(days=7)
    avg_7_hari = full_data[full_data['Tanggal'] >= seminggu_lalu]['Gula Darah'].mean()
    avg_filtered = df_filtered['Gula Darah'].mean()
    min_val = df_filtered['Gula Darah'].min()
    max_val = df_filtered['Gula Darah'].max()
    count_cek = len(df_filtered)
    last_val = full_data.iloc[-1]['Gula Darah']

    status_terakhir = "Normal" if last_val < 140 else ("Waspada" if last_val <= 199 else "Tinggi")
    status_color = "#27ae60" if status_terakhir == "Normal" else ("#e67e22" if status_terakhir == "Waspada" else "#c0392b")

    # Rekap per waktu sesi
    rekap_sesi = df_filtered.groupby('Waktu_Bersih')['Gula Darah'].agg(['mean', 'count']).reset_index()
    
    rows_sesi = ""
    for _, r in rekap_sesi.iterrows():
        rows_sesi += f"<tr><td>{r['Waktu_Bersih']}</td><td style='text-align:center;'>{r['count']} kali</td><td style='text-align:right; font-weight:bold;'>{r['mean']:.1f} mg/dL</td></tr>"

    # Ambil 12 data terakhir untuk tabel riwayat ringkas
    df_riwayat_print = df_filtered.sort_values(by=['Tanggal', 'waktu_kode'], ascending=[False, False]).head(12)
    rows_tabel = ""
    for _, r in df_riwayat_print.iterrows():
        tgl = r['Tanggal'].strftime('%d/%m/%Y')
        menu = str(r.get('Menu Makanan', '-')) if pd.notnull(r.get('Menu Makanan')) else '-'
        catatan = str(r.get('Catatan', '-')) if pd.notnull(r.get('Catatan')) else '-'
        gd = int(r['Gula Darah'])
        
        # Pewarnaan baris nilai GD
        warna_gd = "#27ae60" if gd < 140 else ("#d35400" if gd <= 180 else "#c0392b")

        rows_tabel += f"""
        <tr>
            <td style='text-align:center;'>{tgl}</td>
            <td>{r['Waktu_Bersih']}</td>
            <td style='text-align:center; font-weight:bold; color:{warna_gd};'>{gd}</td>
            <td style='font-size:8.5pt;'>{menu}</td>
            <td style='font-size:8.5pt;'>{catatan}</td>
        </tr>
        """

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Laporan Pemantauan Gula Darah - Sugiyo RH</title>
        <style>
            @page {{
                size: A4 portrait;
                margin: 10mm 12mm;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                color: #222;
                margin: 0;
                padding: 0;
                font-size: 9.5pt;
                line-height: 1.3;
            }}
            .header {{
                border-bottom: 2px solid #2b7bba;
                padding-bottom: 8px;
                margin-bottom: 12px;
            }}
            .title {{
                font-size: 16pt;
                font-weight: bold;
                color: #1a4d73;
                margin: 0;
            }}
            .subtitle {{
                font-size: 8.5pt;
                color: #555;
                margin-top: 3px;
            }}
            .kpi-container {{
                display: table;
                width: 100%;
                margin-bottom: 12px;
            }}
            .kpi-box {{
                display: table-cell;
                width: 25%;
                background: #f4f8fa;
                border: 1px solid #d8e5ed;
                border-radius: 4px;
                padding: 8px 10px;
                text-align: center;
                vertical-align: middle;
            }}
            .kpi-box + .kpi-box {{
                border-left: none;
            }}
            .kpi-val {{
                font-size: 13pt;
                font-weight: bold;
                color: #1a4d73;
                margin-top: 2px;
            }}
            .kpi-lbl {{
                font-size: 7.5pt;
                text-transform: uppercase;
                color: #666;
                letter-spacing: 0.5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 12px;
                font-size: 8.5pt;
            }}
            th {{
                background-color: #eaf1f6;
                color: #1a4d73;
                border: 1px solid #c2d6e4;
                padding: 5px 7px;
                font-weight: bold;
                text-align: left;
            }}
            td {{
                border: 1px solid #dce5ec;
                padding: 4px 7px;
            }}
            tr:nth-child(even) {{
                background-color: #fafbfc;
            }}
            .section-title {{
                font-size: 10.5pt;
                font-weight: bold;
                color: #1a4d73;
                border-left: 3px solid #2b7bba;
                padding-left: 6px;
                margin: 10px 0 6px 0;
            }}
            .footer-sign {{
                margin-top: 15px;
                display: table;
                width: 100%;
            }}
            .sign-box {{
                display: table-cell;
                width: 50%;
                font-size: 8.5pt;
            }}
            .sign-line {{
                margin-top: 40px;
                border-top: 1px dashed #777;
                width: 160px;
            }}
            .btn-print {{
                background-color: #2b7bba;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12pt;
                border-radius: 4px;
                cursor: pointer;
                margin-bottom: 15px;
            }}
            @media print {{
                .no-print {{
                    display: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print" style="background:#e8f4fd; padding:10px; border-radius:6px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
            <span>💡 <i>Klik tombol di sebelah kanan untuk langsung mencetak atau menyimpan dokumen sebagai file PDF A4.</i></span>
            <button class="btn-print" onclick="window.print()">🖨️ Cetak / Simpan PDF</button>
        </div>

        <div class="header">
            <h1 class="title">🩺 Laporan Pemantauan Gula Darah Mandiri</h1>
            <div class="subtitle">
                <b>Nama Pasien:</b> Sugiyo RH | <b>Rentang Filter:</b> {date_str}<br>
                <b>Regimen Terapi:</b> 3x Metformin 500 mg, 2x Gliclazide 80 mg, 1x Insulin Ryzodeg
            </div>
        </div>

        <!-- KPI Cards -->
        <div class="kpi-container">
            <div class="kpi-box">
                <div class="kpi-lbl">Rata-rata 7 Hari</div>
                <div class="kpi-val">{avg_7_hari:.1f} <span style="font-size:8pt;">mg/dL</span></div>
            </div>
            <div class="kpi-box">
                <div class="kpi-lbl">Rata-rata Terpilih</div>
                <div class="kpi-val">{avg_filtered:.1f} <span style="font-size:8pt;">mg/dL</span></div>
            </div>
            <div class="kpi-box">
                <div class="kpi-lbl">Rentang (Min - Max)</div>
                <div class="kpi-val">{min_val:.0f} - {max_val:.0f} <span style="font-size:8pt;">mg/dL</span></div>
            </div>
            <div class="kpi-box">
                <div class="kpi-lbl">Status Terakhir</div>
                <div class="kpi-val" style="color:{status_color};">{status_terakhir} ({last_val:.0f})</div>
            </div>
        </div>

        <!-- Rata-rata per Sesi Waktu -->
        <div class="section-title">📊 Ringkasan Rata-rata per Waktu Pemeriksaan</div>
        <table>
            <thead>
                <tr>
                    <th>Sesi Pemeriksaan</th>
                    <th style="text-align:center; width:20%;">Jumlah Pengukuran</th>
                    <th style="text-align:right; width:25%;">Rata-rata Gula Darah</th>
                </tr>
            </thead>
            <tbody>
                {rows_sesi}
            </tbody>
        </table>

        <!-- Tabel Riwayat Terbaru -->
        <div class="section-title">📋 Riwayat Pemeriksaan Terkini ({len(df_riwayat_print)} Data Terakhir)</div>
        <table>
            <thead>
                <tr>
                    <th style="width:12%; text-align:center;">Tanggal</th>
                    <th style="width:25%;">Waktu Cek</th>
                    <th style="width:12%; text-align:center;">Gula (mg/dL)</th>
                    <th style="width:28%;">Menu Makanan</th>
                    <th style="width:23%;">Catatan Tambahan</th>
                </tr>
            </thead>
            <tbody>
                {rows_tabel}
            </tbody>
        </table>

        <!-- Catatan Target Medis Standar -->
        <div style="font-size:8pt; background-color:#f9f9f9; border:1px solid #eee; padding:6px 10px; border-radius:4px; margin-top:5px;">
            <b>Batas Rekomendasi (PERKENI):</b> Puasa / Sebelum Makan: <b>80 - 130 mg/dL</b> | 2 Jam Setelah Makan: <b>&lt; 180 mg/dL</b>
        </div>

        <!-- Tanda Tangan Dokter / Pasien -->
        <div class="footer-sign">
            <div class="sign-box">
                <div>Catatan Dokter Pemeriksa:</div>
                <div style="margin-top:35px; border-bottom:1px solid #bbb; width:80%;"></div>
            </div>
            <div class="sign-box" style="text-align:right;">
                <div>Mengetahui / Dicetak pada: <b>{pd.Timestamp.now().strftime('%d/%m/%Y')}</b></div>
                <div style="margin-top:35px; margin-left:auto; border-bottom:1px solid #bbb; width:150px; text-align:center;">Sugiyo RH</div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_code


# 3. Header Dashboard
col_title, col_btn = st.columns([3, 1])

with col_title:
    st.title("🩺 Pemantauan Gula Darah Mandiri Sugiyo RH")
    st.caption("Pengobatan: oral + insulin | Dosis: 3x metformin 500 mg, 2x gliclazide 80mg, 1x insulin ryzodeg")

# 4. Filter di Sidebar
with st.sidebar:
    st.header("🔍 Filter Data")
    min_date = data['Tanggal'].min().date()
    max_date = data['Tanggal'].max().date()
    date_range = st.date_input("Pilih Rentang Tanggal:", [min_date, max_date])

    list_waktu = ["Semua"] + sorted([w for w in data['Waktu'].dropna().unique()])
    selected_waktu = st.selectbox("Pilih Waktu Pemeriksaan:", list_waktu)

# Terapkan Filter
filtered_df = data.copy()
date_label = "Semua Periode"
if len(date_range) == 2:
    start_d, end_d = date_range
    filtered_df = filtered_df[(filtered_df['Tanggal'].dt.date >= start_d) & (filtered_df['Tanggal'].dt.date <= end_d)]
    date_label = f"{start_d.strftime('%d/%m/%Y')} s.d. {end_d.strftime('%d/%m/%Y')}"

if selected_waktu != "Semua":
    filtered_df = filtered_df[filtered_df['Waktu'] == selected_waktu]

# -------------------------------------------------------------
# TOMBOL CETAK LAPORAN DENGAN MODAL / EXPANDER DI HALAMAN
# -------------------------------------------------------------
with col_btn:
    st.write("")  # spacer
    tombol_cetak = st.button("🖨️ Cetak Laporan A4", use_container_width=True, type="primary")

if tombol_cetak:
    st.markdown("### 🖨️ Pratinjau Dokumen Cetak A4")
    st.info("Klik tombol **Cetak / Simpan PDF** di dalam kotak pratinjau di bawah ini untuk membuka dialog print browser.")
    html_report = generate_print_html(filtered_df, data, date_label)
    components.html(html_report, height=650, scrolling=True)
    st.divider()

# 5. Ringkasan Metrik (KPI)
st.markdown("### 📊 Ringkasan")
col1, col2, col3, col4 = st.columns(4)

terakhir_tgl = data['Tanggal'].max()
seminggu_lalu = terakhir_tgl - pd.Timedelta(days=7)
avg_7_hari = data[data['Tanggal'] >= seminggu_lalu]['Gula Darah'].mean()
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
    st.markdown(f"**Status Terakhir:**<br><span style='color:{warna}; font-size: 20px; font-weight: bold;'>{kategori}</span>", unsafe_allow_html=True)

st.divider()

# 6. Tab Visualisasi & Data
tab_tren, tab_mingguan, tab_tabel = st.tabs(["📈 Tren Gula Darah", "📅 Rata-rata Mingguan", "📋 Tabel Riwayat"])

with tab_tren:
    st.subheader("Tren Kadar Gula Darah (Garis Berkelanjutan)")
    if not filtered_df.empty:
        df_plot = filtered_df.sort_values(by=['Tanggal', 'waktu_kode']).copy()
        df_plot['Label_X'] = df_plot['Tanggal'].dt.strftime('%d/%m') + " (" + df_plot['waktu_kode'] + ")"

        fig_tren = go.Figure()

        fig_tren.add_trace(go.Scatter(
            x=df_plot['Label_X'],
            y=df_plot['Gula Darah'],
            mode='lines+markers',
            line=dict(color='#2b7bba', width=3, shape='spline', smoothing=1.2),
            marker=dict(size=9, symbol='star-diamond', color='#2b7bba', line=dict(width=1, color='white')),
            name='Kadar Gula Darah',
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>" +
                "Sesi: <b>%{customdata[1]}</b> (%{x})<br>" +
                "Kadar Gula: <b>%{y} mg/dL</b><br>" +
                "Menu: %{customdata[2]}<br>" +
                "Catatan: %{customdata[3]}<extra></extra>"
            ),
            customdata=df_plot[['Tanggal', 'Waktu', 'Menu Makanan', 'Catatan']].fillna('-').assign(
                Tanggal=df_plot['Tanggal'].dt.strftime('%d/%m/%Y')
            ).values
        ))

        fig_tren.add_hline(
            y=180, line_dash="dot", line_color="#e67e22",
            annotation_text="Batas Aman Setelah Makan (180 mg/dL)", annotation_position="top left"
        )
        fig_tren.add_hline(
            y=130, line_dash="dot", line_color="#27ae60",
            annotation_text="Batas Sebelum Makan (130 mg/dL)", annotation_position="bottom left"
        )

        fig_tren.update_layout(
            yaxis_title="Gula Darah (mg/dL)",
            xaxis_title="Tanggal & Inisial Waktu (A - G)",
            hovermode="x unified",
            yaxis=dict(range=[0, max(df_plot['Gula Darah'].max() + 50, 250)]),
            xaxis=dict(tickangle=-45),
            margin=dict(l=20, r=20, t=30, b=80),
            template="plotly_white"
        )

        st.plotly_chart(fig_tren, use_container_width=True)

        st.info("""
        **Keterangan Inisial Waktu Sumbu X:**
        * **A**: Sebelum Makan Pagi | **B**: Setelah Makan Pagi
        * **C**: Sebelum Makan Siang | **D**: Setelah Makan Siang
        * **E**: Sebelum Makan Malam | **F**: Setelah Makan Malam
        * **G**: Sebelum Tidur Malam
        """)
    else:
        st.info("Tidak ada data pada filter yang dipilih.")

with tab_mingguan:
    st.subheader("Rata-rata Gula Darah per Pekan")
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
    kolom_tampil = ['Tanggal', 'waktu_kode', 'Waktu', 'Gula Darah', 'Menu Makanan', 'Olahraga', 'Catatan']
    kolom_ada = [c for c in kolom_tampil if c in filtered_df.columns]

    tabel_display = filtered_df[kolom_ada].sort_values(by=['Tanggal', 'waktu_kode'], ascending=[False, False]).copy()
    tabel_display['Tanggal'] = tabel_display['Tanggal'].dt.strftime('%d/%m/%Y')

    st.dataframe(
        tabel_display.rename(columns={'waktu_kode': 'Kode'}),
        use_container_width=True
    )
