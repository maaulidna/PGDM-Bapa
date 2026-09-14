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
  csv_url = f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'
  df = pd.read_csv(csv_url)

  # Perbaikan pada konversi Tanggal: gunakan format='mixed'
  df['Tanggal'] = pd.to_datetime(df['Tanggal'], format='mixed', errors='coerce')
  df['Gula Darah'] = pd.to_numeric(df['Gula Darah'], errors='coerce')
  df = df.dropna(subset=['Tanggal', 'Gula Darah'])

  df['Waktu_Bersih'] = df['Waktu'].astype(str).str.strip()
  df['waktu_kode'] = df['Waktu_Bersih'].map(MAPPING_WAKTU).fillna('Z')
  df = df.sort_values(by=['Tanggal', 'waktu_kode'])

  df['Minggu'] = (
      df['Tanggal']
      .dt.to_period('W')
      .apply(
          lambda r: (
              f"{r.start_time.strftime('%d/%m')} - {r.end_time.strftime('%d/%m')}"
          )
      )
  )
  return df

try:
    data = load_data()
except Exception as e:
    st.error(f"Gagal mengambil data dari Google Sheets: {e}")
    st.stop()

# ----------------------------------------------------------------------
# FUNGSI MEMBUAT LAPORAN MULTI-HALAMAN A4 CETAK LENGKAP
# ----------------------------------------------------------------------
def generate_multi_page_report_html(df_filtered, full_data, date_str):
    terakhir_tgl = full_data['Tanggal'].max()
    seminggu_lalu = terakhir_tgl - pd.Timedelta(days=7)
    avg_7_hari = full_data[full_data['Tanggal'] >= seminggu_lalu]['Gula Darah'].mean()
    avg_filtered = df_filtered['Gula Darah'].mean()
    min_val = df_filtered['Gula Darah'].min()
    max_val = df_filtered['Gula Darah'].max()
    total_cek = len(df_filtered)
    last_val = full_data.iloc[-1]['Gula Darah']

    status_terakhir = "Normal" if last_val < 140 else ("Waspada" if last_val <= 199 else "Tinggi")
    status_color = "#27ae60" if status_terakhir == "Normal" else ("#e67e22" if status_terakhir == "Waspada" else "#c0392b")

    # Rekap per Sesi
    rekap_sesi = df_filtered.groupby('Waktu_Bersih')['Gula Darah'].agg(['mean', 'min', 'max', 'count']).reset_index()
    rekap_sesi['kode'] = rekap_sesi['Waktu_Bersih'].map(MAPPING_WAKTU).fillna('Z')
    rekap_sesi = rekap_sesi.sort_values('kode')

    rows_sesi = ""
    for _, r in rekap_sesi.iterrows():
        rows_sesi += f"""
        <tr>
            <td><b>({r['kode']})</b> {r['Waktu_Bersih']}</td>
            <td style='text-align:center;'>{r['count']}x</td>
            <td style='text-align:center;'>{r['min']:.0f} - {r['max']:.0f}</td>
            <td style='text-align:right; font-weight:bold;'>{r['mean']:.1f} mg/dL</td>
        </tr>
        """

    # Rekap Mingguan
    df_wk = df_filtered.groupby('Minggu')['Gula Darah'].agg(['mean', 'count']).reset_index()
    rows_mingguan = ""
    for _, r in df_wk.iterrows():
        rows_mingguan += f"""
        <tr>
            <td>{r['Minggu']}</td>
            <td style='text-align:center;'>{r['count']}x</td>
            <td style='text-align:right; font-weight:bold;'>{r['mean']:.1f} mg/dL</td>
        </tr>
        """

    # Render Grafik Tren Plotly (dikonfigurasi proporsional untuk Halaman 1 A4)
    df_plot = df_filtered.sort_values(by=['Tanggal', 'waktu_kode']).copy()
    df_plot['Label_X'] = df_plot['Tanggal'].dt.strftime('%d/%m') + " (" + df_plot['waktu_kode'] + ")"

    fig_tren = go.Figure()
    fig_tren.add_trace(go.Scatter(
        x=df_plot['Label_X'],
        y=df_plot['Gula Darah'],
        mode='lines+markers+text',
        text=df_plot['Gula Darah'].astype(int).astype(str),
        textposition="top center",
        textfont=dict(size=8, color="#0f3756"),
        line=dict(color='#2b7bba', width=2),
        marker=dict(size=6, color='#1a4d73'),
        name='Gula Darah'
    ))
    fig_tren.add_hline(
        y=180, line_dash="dash", line_color="#d35400", line_width=1.5,
        annotation_text="Batas Atas Setelah Makan (180 mg/dL)", annotation_position="top left",
        annotation_font=dict(size=8.5, color="#d35400")
    )
    fig_tren.add_hline(
        y=130, line_dash="dash", line_color="#27ae60", line_width=1.5,
        annotation_text="Target Sebelum Makan (130 mg/dL)", annotation_position="bottom left",
        annotation_font=dict(size=8.5, color="#27ae60")
    )
    fig_tren.update_layout(
        height=300,
        margin=dict(l=35, r=15, t=20, b=70),
        yaxis=dict(title="Kadar (mg/dL)", range=[0, max(df_plot['Gula Darah'].max() + 45, 230)], tickfont=dict(size=8)),
        xaxis=dict(tickangle=-55, tickfont=dict(size=8)),
        template="plotly_white",
        showlegend=False
    )
    grafik_div = fig_tren.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})

    # Seluruh Baris Data Riwayat Lengkap Tanpa Batasan Limit
    tabel_lengkap = df_filtered.sort_values(by=['Tanggal', 'waktu_kode'], ascending=[False, False]).copy()
    rows_detail = ""
    for idx, (_, r) in enumerate(tabel_lengkap.iterrows(), start=1):
        tgl = r['Tanggal'].strftime('%d/%m/%Y')
        sesi = f"({r['waktu_kode']}) {r['Waktu_Bersih']}"
        gd = int(r['Gula Darah'])
        menu = str(r.get('Menu Makanan', '-')) if pd.notnull(r.get('Menu Makanan')) and str(r.get('Menu Makanan')).strip() != '' else '-'
        olahraga = str(r.get('Olahraga', '-')) if pd.notnull(r.get('Olahraga')) and str(r.get('Olahraga')).strip() != '' else '-'
        catatan = str(r.get('Catatan', '-')) if pd.notnull(r.get('Catatan')) and str(r.get('Catatan')).strip() != '' else '-'

        warna_gd = "#27ae60" if gd < 140 else ("#d35400" if gd <= 180 else "#c0392b")

        rows_detail += f"""
        <tr>
            <td style='text-align:center; color:#777;'>{idx}</td>
            <td style='text-align:center; white-space:nowrap;'>{tgl}</td>
            <td style='white-space:nowrap;'>{sesi}</td>
            <td style='text-align:center; font-weight:bold; color:{warna_gd}; font-size:9.5pt;'>{gd}</td>
            <td>{menu}</td>
            <td>{olahraga}</td>
            <td>{catatan}</td>
        </tr>
        """

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Laporan Lengkap Rekam Medis Gula Darah - Sugiyo RH</title>
        <style>
            @page {{
                size: A4 portrait;
                margin: 12mm 14mm 14mm 14mm;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                color: #222;
                margin: 0;
                padding: 0;
                font-size: 8.5pt;
                line-height: 1.35;
            }}
            .no-print {{
                background: #eef6fc;
                border: 1px solid #c9e2f5;
                padding: 10px 14px;
                border-radius: 6px;
                margin-bottom: 14px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .btn-print {{
                background-color: #2b7bba;
                color: white;
                border: none;
                padding: 9px 18px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 4px;
                cursor: pointer;
            }}
            .header {{
                border-bottom: 2px solid #1a4d73;
                padding-bottom: 6px;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 15pt;
                font-weight: bold;
                color: #1a4d73;
                margin: 0;
            }}
            .subtitle {{
                font-size: 8pt;
                color: #444;
                margin-top: 3px;
            }}
            .kpi-container {{
                display: table;
                width: 100%;
                margin-bottom: 10px;
            }}
            .kpi-box {{
                display: table-cell;
                width: 20%;
                background: #f7fafc;
                border: 1px solid #d5e3ec;
                padding: 6px 8px;
                text-align: center;
                vertical-align: middle;
            }}
            .kpi-box + .kpi-box {{
                border-left: none;
            }}
            .kpi-val {{
                font-size: 12.5pt;
                font-weight: bold;
                color: #1a4d73;
            }}
            .kpi-lbl {{
                font-size: 7pt;
                text-transform: uppercase;
                color: #666;
                font-weight: bold;
            }}
            .section-title {{
                font-size: 9.5pt;
                font-weight: bold;
                color: #1a4d73;
                border-left: 3px solid #2b7bba;
                padding-left: 6px;
                margin: 10px 0 6px 0;
            }}
            .split-container {{
                display: table;
                width: 100%;
                margin-bottom: 8px;
            }}
            .split-left {{
                display: table-cell;
                width: 58%;
                vertical-align: top;
                padding-right: 8px;
            }}
            .split-right {{
                display: table-cell;
                width: 42%;
                vertical-align: top;
                padding-left: 8px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 8px;
                font-size: 8pt;
            }}
            th {{
                background-color: #eaf1f6 !important;
                color: #1a4d73;
                border: 1px solid #c2d6e4;
                padding: 5px 6px;
                font-weight: bold;
                text-align: left;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            td {{
                border: 1px solid #dce5ec;
                padding: 4px 6px;
                vertical-align: top;
            }}
            tr:nth-child(even) {{
                background-color: #fafbfc;
            }}
            
            /* PENGATURAN CETAK MULTI-HALAMAN */
            .page-break-before {{
                page-break-before: always;
                break-before: page;
            }}
            tr {{
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            thead {{
                display: table-header-group;
            }}
            tfoot {{
                display: table-footer-group;
            }}
            .footer-sign {{
                margin-top: 20px;
                display: table;
                width: 100%;
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            .sign-box {{
                display: table-cell;
                width: 50%;
                font-size: 8pt;
            }}
            .legend-box {{
                background: #fdfefe;
                border: 1px solid #e1e8ed;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 7.5pt;
                margin-top: 4px;
                margin-bottom: 6px;
            }}
            @media print {{
                .no-print {{
                    display: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print">
            <div>
                <b>Pratinjau Dokumen Cetak Lengkap (Multi-Halaman A4)</b><br>
                <span style="font-size:8.5pt; color:#555;">Dokumen otomatis terbagi menjadi beberapa lembar A4 rapi tanpa memotong tabel.</span>
            </div>
            <button class="btn-print" onclick="window.print()">🖨️ Cetak / Unduh PDF</button>
        </div>

        <!-- ================= HALAMAN 1: DASBOR & GRAFIK ================= -->
        <div class="header">
            <h1 class="title">🩺 Rekam Pemantauan Gula Darah Mandiri</h1>
            <div class="subtitle">
                <b>Nama Pasien:</b> Sugiyo RH &nbsp;|&nbsp; <b>Periode Data:</b> {date_str} &nbsp;|&nbsp; <b>Total Pengukuran:</b> {total_cek} kali<br>
                <b>Pengobatan:</b> 3x Metformin 500 mg, 2x Gliclazide 80 mg, 1x Insulin Ryzodeg
            </div>
        </div>

        <div class="kpi-container">
            <div class="kpi-box">
                <div class="kpi-lbl">Rata-rata Terpilih</div>
                <div class="kpi-val">{avg_filtered:.1f} <span style="font-size:7.5pt;">mg/dL</span></div>
            </div>
            <div class="kpi-box">
                <div class="kpi-lbl">Rata-rata 7 Hari</div>
                <div class="kpi-val">{avg_7_hari:.1f} <span style="font-size:7.5pt;">mg/dL</span></div>
            </div>
            <div class="kpi-box">
                <div class="kpi-lbl">Gula Terendah</div>
                <div class="kpi-val" style="color:#27ae60;">{min_val:.0f} <span style="font-size:7.5pt;">mg/dL</span></div>
            </div>
            <div class="kpi-box">
                <div class="kpi-lbl">Gula Tertinggi</div>
                <div class="kpi-val" style="color:#c0392b;">{max_val:.0f} <span style="font-size:7.5pt;">mg/dL</span></div>
            </div>
            <div class="kpi-box">
                <div class="kpi-lbl">Status Terakhir</div>
                <div class="kpi-val" style="color:{status_color};">{status_terakhir} ({last_val:.0f})</div>
            </div>
        </div>

        <div class="section-title">📈 Grafik Tren Kadar Gula Darah Detail</div>
        <div style="width: 100%; border: 1px solid #dce5ec; border-radius: 4px; padding: 3px; background:#fff;">
            {grafik_div}
        </div>

        <div class="legend-box">
            <b>Inisial Sumbu X:</b> A = Sebelum Makan Pagi | B = Setelah Makan Pagi | C = Sebelum Makan Siang | D = Setelah Makan Siang | E = Sebelum Makan Malam | F = Setelah Makan Malam | G = Sebelum Tidur
        </div>

        <div class="split-container">
            <div class="split-left">
                <div class="section-title">📊 Rata-rata per Sesi Pengukuran</div>
                <table>
                    <thead>
                        <tr>
                            <th>Sesi Waktu</th>
                            <th style="text-align:center;">Jml</th>
                            <th style="text-align:center;">Rentang</th>
                            <th style="text-align:right;">Rata-rata</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_sesi}
                    </tbody>
                </table>
            </div>
            <div class="split-right">
                <div class="section-title">📅 Rata-rata Mingguan</div>
                <table>
                    <thead>
                        <tr>
                            <th>Pekan</th>
                            <th style="text-align:center;">Jml</th>
                            <th style="text-align:right;">Rata-rata</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_mingguan}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- ================= HALAMAN 2+: TABEL DETAIL LENGKAP ================= -->
        <div class="page-break-before"></div>

        <div class="section-title" style="font-size:11pt; border-left:4px solid #2b7bba; padding-left:8px; margin-top:5px;">
            📋 Tabel Log Riwayat Pemeriksaan Lengkap ({total_cek} Catatan)
        </div>
        <div style="font-size:7.5pt; color:#666; margin-bottom:8px;">
            Urutan data kronologis terbalik (terbaru ke terlama) beserta catatan asupan nutrisi dan keluhan.
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width:4%; text-align:center;">No</th>
                    <th style="width:11%; text-align:center;">Tanggal</th>
                    <th style="width:20%;">Waktu Sesi</th>
                    <th style="width:11%; text-align:center;">Gula (mg/dL)</th>
                    <th style="width:24%;">Menu Makanan</th>
                    <th style="width:14%;">Olahraga</th>
                    <th style="width:16%;">Catatan Tambahan</th>
                </tr>
            </thead>
            <tbody>
                {rows_detail}
            </tbody>
        </table>

        <!-- Kolom Verifikasi & Catatan Klinis di Lembar Terakhir -->
        <div class="footer-sign">
            <div class="sign-box">
                <div><b>Catatan / Evaluasi Dokter Spesialis / Faskes:</b></div>
                <div style="margin-top:40px; border-bottom:1px solid #777; width:85%;"></div>
            </div>
            <div class="sign-box" style="text-align:right;">
                <div>Tanggal Cetak: <b>{pd.Timestamp.now().strftime('%d/%m/%Y')}</b></div>
                <div style="margin-top:40px; margin-left:auto; border-bottom:1px solid #777; width:160px; text-align:center;">Sugiyo RH</div>
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

# Tombol Cetak Laporan
with col_btn:
    st.write("")
    tombol_cetak = st.button("🖨️ Cetak Laporan Lengkap A4", use_container_width=True, type="primary")

if tombol_cetak:
    st.markdown("### 🖨️ Pratinjau Dokumen Cetak Lengkap (Multi-Halaman)")
    st.info("Dokumen ini memuat dasbor grafik dan seluruh baris log riwayat. Klik tombol **Cetak / Unduh PDF** di dalam kotak pratinjau untuk mencetak/menyimpan PDF.")
    html_report = generate_multi_page_report_html(filtered_df, data, date_label)
    components.html(html_report, height=750, scrolling=True)
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
