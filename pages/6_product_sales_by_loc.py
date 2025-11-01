import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="📊 Sales by Location", layout="wide")
st.title("📊 Laporan Penjualan per Produk & Lokasi")

db = st.secrets["connections"]["neon"]

# 🔌 Koneksi database
@st.cache_data
def get_data(query):
    conn = psycopg2.connect(
        host=db["host"],
        database=db["database"],
        user=db["user"],
        password=db["password"],
        port=db["port"],
        sslmode=db.get("sslmode", "require")
    )
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# 🔍 Ambil master dropdown untuk produk (gabungan kode + nama)
produk_df = get_data("""
    SELECT DISTINCT "kodeProduk", "namaProduk",
           CONCAT("kodeProduk", ' - ', "namaProduk") as produk_display
    FROM sales_data 
    WHERE "kodeProduk" IS NOT NULL AND "namaProduk" IS NOT NULL
    ORDER BY "kodeProduk"
""")

loc_df = get_data("""
    SELECT DISTINCT loccd 
    FROM sales_data 
    WHERE loccd IS NOT NULL 
    ORDER BY loccd
""")

# 📋 Form Filter
st.subheader("🎯 Filter Data Penjualan")

with st.form("filter_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_type = st.selectbox("Pilih jenis tanggal:", ["createdt", "batchdt", "bnsperiod"])
        # Tanggal mulai dan akhir di bawah jenis tanggal
        start_date = st.date_input("Tanggal Mulai")
        end_date = st.date_input("Tanggal Akhir")
    
    with col2:
        # Dropdown produk yang menggabungkan kode dan nama
        produk_options = ["ALL"] + sorted(produk_df["produk_display"].unique().tolist())
        selected_produk = st.selectbox("Pilih Produk", produk_options)
        
    with col3:
        loccd = st.selectbox("Kode Lokasi", ["ALL"] + sorted(loc_df["loccd"].tolist()))

    submitted = st.form_submit_button("🚀 Jalankan Query")

# 📊 Jalankan query hanya setelah submit
if submitted:
    try:
        conn = psycopg2.connect(
            host=db["host"],
            database=db["database"],
            user=db["user"],
            password=db["password"],
            port=db["port"],
            sslmode=db.get("sslmode", "require")
        )

        # Ekstrak kodeProduk dari pilihan yang digabung
        if selected_produk != "ALL":
            kode_produk_selected = selected_produk.split(" - ")[0]
            nama_produk_selected = selected_produk.split(" - ")[1]
        else:
            kode_produk_selected = "ALL"
            nama_produk_selected = "ALL"

        query = f"""
            SELECT 
                bnsperiod,
                loccd,
                "kodeProduk",
                "namaProduk",
                SUM("totalQty_contrib"::numeric) AS total_qty
            FROM sales_data
            WHERE ("{date_type}"::date) BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if selected_produk != "ALL":
            query += ' AND "kodeProduk" = %s AND "namaProduk" = %s'
            params.append(kode_produk_selected)
            params.append(nama_produk_selected)

        if loccd != "ALL":
            query += ' AND loccd = %s'
            params.append(loccd)

        query += """
            GROUP BY bnsperiod, loccd, "kodeProduk", "namaProduk"
            ORDER BY bnsperiod DESC, loccd, total_qty DESC
        """

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if not df.empty:
            st.success(f"✅ {len(df)} baris ditemukan.")
            
            # Tampilkan summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Total Quantity", f"{df['total_qty'].sum():,.0f}")
            with col3:
                st.metric("Unique Products", df['namaProduk'].nunique())
            with col4:
                st.metric("Unique Locations", df['loccd'].nunique())
            
            st.dataframe(df, use_container_width=True)

            # 💾 Download tombol
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="sales_by_location.csv",
                mime="text/csv",
            )
            
            # 📊 VISUALISASI YANG BAGUS DAN INFORMATIF
            st.markdown("---")
            st.subheader("📈 Dashboard Visualisasi Penjualan")
            
            # Tab untuk berbagai jenis visualisasi
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏆 Top Performers", 
                "📊 Tren Bulanan", 
                "🗺️ Distribusi Geografis", 
                "📦 Performance Produk", 
                "📈 Analisis Komparatif"
            ])
            
            with tab1:
                # TOP PERFORMERS
                col1, col2 = st.columns(2)
                
                with col1:
                    # Top 10 Products
                    top_products = df.groupby('namaProduk')['total_qty'].sum().nlargest(10).reset_index()
                    fig_products = px.bar(
                        top_products, 
                        x='total_qty', 
                        y='namaProduk',
                        orientation='h',
                        title='🏆 10 Produk Terlaris',
                        color='total_qty',
                        color_continuous_scale='viridis'
                    )
                    fig_products.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_products, use_container_width=True)
                
                with col2:
                    # Top 10 Locations
                    top_locations = df.groupby('loccd')['total_qty'].sum().nlargest(10).reset_index()
                    fig_locations = px.bar(
                        top_locations,
                        x='total_qty',
                        y='loccd',
                        orientation='h',
                        title='📍 10 Lokasi Terbaik',
                        color='total_qty',
                        color_continuous_scale='plasma'
                    )
                    fig_locations.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_locations, use_container_width=True)
            
            with tab2:
                # TREN BULANAN
                col1, col2 = st.columns(2)
                
                with col1:
                    # Tren bulanan total
                    monthly_trend = df.groupby('bnsperiod')['total_qty'].sum().reset_index()
                    fig_trend = px.line(
                        monthly_trend,
                        x='bnsperiod',
                        y='total_qty',
                        title='📈 Tren Penjualan Bulanan',
                        markers=True
                    )
                    fig_trend.update_traces(line=dict(width=3))
                    fig_trend.update_layout(height=400)
                    st.plotly_chart(fig_trend, use_container_width=True)
                
                with col2:
                    # Heatmap bulanan per produk
                    heatmap_data = df.pivot_table(
                        values='total_qty', 
                        index='namaProduk', 
                        columns='bnsperiod', 
                        aggfunc='sum'
                    ).fillna(0)
                    
                    if not heatmap_data.empty:
                        fig_heatmap = px.imshow(
                            heatmap_data,
                            title='🔥 Heatmap Produk vs Periode',
                            color_continuous_scale='YlOrRd',
                            aspect="auto"
                        )
                        fig_heatmap.update_layout(height=400)
                        st.plotly_chart(fig_heatmap, use_container_width=True)
            
            with tab3:
                # DISTRIBUSI GEOGRAFIS
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pie chart distribusi lokasi
                    loc_distribution = df.groupby('loccd')['total_qty'].sum().reset_index()
                    fig_pie = px.pie(
                        loc_distribution,
                        values='total_qty',
                        names='loccd',
                        title='🥧 Distribusi Penjualan per Lokasi',
                        hole=0.4
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(height=500)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Treemap untuk visualisasi hierarkis
                    treemap_data = df.groupby(['loccd', 'namaProduk'])['total_qty'].sum().reset_index()
                    fig_treemap = px.treemap(
                        treemap_data,
                        path=['loccd', 'namaProduk'],
                        values='total_qty',
                        title='🌳 Struktur Penjualan (Lokasi → Produk)',
                        color='total_qty',
                        color_continuous_scale='RdYlGn'
                    )
                    fig_treemap.update_layout(height=500)
                    st.plotly_chart(fig_treemap, use_container_width=True)
            
            with tab4:
                # PERFORMANCE PRODUK
                col1, col2 = st.columns(2)
                
                with col1:
                    # Scatter plot - produk performance
                    product_performance = df.groupby('namaProduk').agg({
                        'total_qty': 'sum',
                        'loccd': 'nunique'
                    }).reset_index()
                    product_performance.columns = ['namaProduk', 'total_qty', 'jumlah_lokasi']
                    
                    fig_scatter = px.scatter(
                        product_performance,
                        x='jumlah_lokasi',
                        y='total_qty',
                        size='total_qty',
                        color='total_qty',
                        hover_name='namaProduk',
                        title='🎯 Performance Produk vs Jangkauan Lokasi',
                        size_max=50,
                        color_continuous_scale='rainbow'
                    )
                    fig_scatter.update_layout(height=500)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                with col2:
                    # Donut chart market share produk
                    market_share = df.groupby('namaProduk')['total_qty'].sum().reset_index()
                    fig_donut = px.pie(
                        market_share,
                        values='total_qty',
                        names='namaProduk',
                        title='🎯 Market Share Produk',
                        hole=0.6
                    )
                    fig_donut.update_traces(textinfo='percent+label')
                    fig_donut.update_layout(height=500, showlegend=False)
                    st.plotly_chart(fig_donut, use_container_width=True)
            
            with tab5:
                # ANALISIS KOMPARATIF
                col1, col2 = st.columns(2)
                
                with col1:
                    # Radar chart untuk perbandingan produk
                    radar_data = df.groupby(['namaProduk', 'loccd'])['total_qty'].sum().reset_index()
                    top_5_products = df.groupby('namaProduk')['total_qty'].sum().nlargest(5).index
                    radar_data = radar_data[radar_data['namaProduk'].isin(top_5_products)]
                    
                    # Pivot untuk radar chart
                    pivot_radar = radar_data.pivot(index='loccd', columns='namaProduk', values='total_qty').fillna(0)
                    
                    fig_radar = go.Figure()
                    for product in pivot_radar.columns:
                        fig_radar.add_trace(go.Scatterpolar(
                            r=pivot_radar[product].values,
                            theta=pivot_radar.index,
                            fill='toself',
                            name=product
                        ))
                    
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True)),
                        title='🔄 Perbandingan Produk di Berbagai Lokasi (Radar Chart)',
                        height=500
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                
                with col2:
                    # Area chart tren kumulatif
                    df_sorted = df.sort_values('bnsperiod')
                    cumulative_data = df_sorted.groupby(['bnsperiod', 'namaProduk'])['total_qty'].sum().reset_index()
                    cumulative_data['cumulative'] = cumulative_data.groupby('namaProduk')['total_qty'].cumsum()
                    
                    fig_area = px.area(
                        cumulative_data,
                        x='bnsperiod',
                        y='cumulative',
                        color='namaProduk',
                        title='📊 Tren Kumulatif Penjualan per Produk',
                        height=500
                    )
                    st.plotly_chart(fig_area, use_container_width=True)
                    
        else:
            st.warning("⚠️ Tidak ada data ditemukan untuk filter tersebut.")
            
    except Exception as e:
        st.error(f"❌ Error saat menjalankan query: {e}")

# ℹ️ Informasi penggunaan
with st.expander("ℹ️ Cara Penggunaan"):
    st.markdown("""
    ### 📋 Panduan Penggunaan Dashboard
    
    1. **Filter Data**: Pilih jenis tanggal, rentang waktu, produk, dan lokasi
    2. **Jalankan Query**: Klik tombol 'Jalankan Query' untuk memproses data
    3. **Analisis Visual**: Jelajahi berbagai visualisasi di 5 tab berbeda:
       - **🏆 Top Performers**: Produk dan lokasi terbaik
       - **📊 Tren Bulanan**: Perkembangan penjualan over time
       - **🗺️ Distribusi Geografis**: Penyebaran penjualan per lokasi
       - **📦 Performance Produk**: Analisis mendalam per produk
       - **📈 Analisis Komparatif**: Perbandingan multi-dimensi
    
    4. **Download Data**: Export hasil dalam format CSV untuk analisis lebih lanjut
    """)
