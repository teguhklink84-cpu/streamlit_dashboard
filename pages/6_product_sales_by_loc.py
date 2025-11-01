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
        # MULTI-SELECT untuk produk menggunakan multiselect
        produk_options = sorted(produk_df["produk_display"].unique().tolist())
        selected_produk = st.multiselect(
            "Pilih Produk (bisa pilih lebih dari 1):",
            options=produk_options,
            placeholder="Pilih satu atau lebih produk..."
        )
        
    with col3:
        # MULTI-SELECT untuk lokasi menggunakan multiselect
        loc_options = sorted(loc_df["loccd"].tolist())
        selected_locations = st.multiselect(
            "Pilih Lokasi (bisa pilih lebih dari 1):",
            options=loc_options,
            placeholder="Pilih satu atau lebih lokasi..."
        )

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

        # Query dasar dengan createdt
        query = f"""
            SELECT 
                bnsperiod,
                createdt,
                loccd,
                "kodeProduk",
                "namaProduk",
                SUM("totalQty_contrib"::numeric) AS total_qty
            FROM sales_data
            WHERE ("{date_type}"::date) BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        # Filter untuk produk (bisa multiple)
        if selected_produk:
            produk_conditions = []
            for produk in selected_produk:
                kode_produk_selected = produk.split(" - ")[0]
                nama_produk_selected = produk.split(" - ")[1]
                produk_conditions.append(f'("kodeProduk" = %s AND "namaProduk" = %s)')
                params.extend([kode_produk_selected, nama_produk_selected])
            
            if produk_conditions:
                query += " AND (" + " OR ".join(produk_conditions) + ")"

        # Filter untuk lokasi (bisa multiple)
        if selected_locations:
            loc_conditions = []
            for loc in selected_locations:
                loc_conditions.append("loccd = %s")
                params.append(loc)
            
            if loc_conditions:
                query += " AND (" + " OR ".join(loc_conditions) + ")"

        query += """
            GROUP BY bnsperiod, createdt, loccd, "kodeProduk", "namaProduk"
            ORDER BY bnsperiod DESC, createdt DESC, loccd, total_qty DESC
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
            
            # Tampilkan dataframe dengan createdt
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
                "📊 Tren Berdasarkan Tanggal", 
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
                # TREN BERDASARKAN TANGGAL YANG DIPILIH
                st.subheader(f"📈 Tren Berdasarkan {date_type}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Tren berdasarkan date_type yang dipilih
                    if date_type == 'createdt':
                        trend_data = df.groupby('createdt')['total_qty'].sum().reset_index()
                        x_col = 'createdt'
                    elif date_type == 'batchdt':
                        # Jika perlu menambahkan batchdt ke query
                        trend_data = df.groupby('bnsperiod')['total_qty'].sum().reset_index()
                        x_col = 'bnsperiod'
                    else:  # bnsperiod
                        trend_data = df.groupby('bnsperiod')['total_qty'].sum().reset_index()
                        x_col = 'bnsperiod'
                    
                    fig_trend = px.line(
                        trend_data,
                        x=x_col,
                        y='total_qty',
                        title=f'📈 Tren Penjualan Berdasarkan {date_type}',
                        markers=True
                    )
                    fig_trend.update_traces(line=dict(width=3))
                    fig_trend.update_layout(height=400)
                    st.plotly_chart(fig_trend, use_container_width=True)
                
                with col2:
                    # Tren dengan breakdown produk
                    if date_type == 'createdt':
                        trend_by_product = df.groupby(['createdt', 'namaProduk'])['total_qty'].sum().reset_index()
                        x_col_product = 'createdt'
                    elif date_type == 'batchdt':
                        trend_by_product = df.groupby(['bnsperiod', 'namaProduk'])['total_qty'].sum().reset_index()
                        x_col_product = 'bnsperiod'
                    else:
                        trend_by_product = df.groupby(['bnsperiod', 'namaProduk'])['total_qty'].sum().reset_index()
                        x_col_product = 'bnsperiod'
                    
                    fig_trend_product = px.line(
                        trend_by_product,
                        x=x_col_product,
                        y='total_qty',
                        color='namaProduk',
                        title=f'📊 Tren Penjualan per Produk ({date_type})',
                        markers=True
                    )
                    fig_trend_product.update_layout(height=400, legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ))
                    st.plotly_chart(fig_trend_product, use_container_width=True)
            
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
                    # Bar chart perbandingan produk di lokasi
                    comparison_data = df.groupby(['namaProduk', 'loccd'])['total_qty'].sum().reset_index()
                    fig_comparison = px.bar(
                        comparison_data,
                        x='loccd',
                        y='total_qty',
                        color='namaProduk',
                        title='📊 Perbandingan Penjualan Produk per Lokasi',
                        barmode='group'
                    )
                    fig_comparison.update_layout(height=500, xaxis_tickangle=-45)
                    st.plotly_chart(fig_comparison, use_container_width=True)
                
                with col2:
                    # Area chart tren kumulatif berdasarkan date_type
                    if date_type == 'createdt':
                        df_sorted = df.sort_values('createdt')
                        cumulative_data = df_sorted.groupby(['createdt', 'namaProduk'])['total_qty'].sum().reset_index()
                        x_col_cumulative = 'createdt'
                    elif date_type == 'batchdt':
                        df_sorted = df.sort_values('bnsperiod')
                        cumulative_data = df_sorted.groupby(['bnsperiod', 'namaProduk'])['total_qty'].sum().reset_index()
                        x_col_cumulative = 'bnsperiod'
                    else:
                        df_sorted = df.sort_values('bnsperiod')
                        cumulative_data = df_sorted.groupby(['bnsperiod', 'namaProduk'])['total_qty'].sum().reset_index()
                        x_col_cumulative = 'bnsperiod'
                    
                    cumulative_data['cumulative'] = cumulative_data.groupby('namaProduk')['total_qty'].cumsum()
                    
                    fig_area = px.area(
                        cumulative_data,
                        x=x_col_cumulative,
                        y='cumulative',
                        color='namaProduk',
                        title=f'📈 Tren Kumulatif Penjualan per Produk ({date_type})',
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
    
    1. **Filter Data**: 
       - Pilih jenis tanggal (createdt, batchdt, atau bnsperiod)
       - Atur rentang waktu mulai dan akhir
       - Pilih satu atau lebih produk (bisa multiple selection)
       - Pilih satu atau lebih lokasi (bisa multiple selection)
    
    2. **Jalankan Query**: Klik tombol 'Jalankan Query' untuk memproses data
    
    3. **Analisis Visual**: Jelajahi berbagai visualisasi di 5 tab berbeda:
       - **🏆 Top Performers**: Produk dan lokasi terbaik
       - **📊 Tren Berdasarkan Tanggal**: Tren berdasarkan tanggal yang dipilih (createdt/batchdt/bnsperiod)
       - **🗺️ Distribusi Geografis**: Penyebaran penjualan per lokasi
       - **📦 Performance Produk**: Analisis mendalam per produk
       - **📈 Analisis Komparatif**: Perbandingan multi-dimensi
    
    4. **Download Data**: Export hasil dalam format CSV untuk analisis lebih lanjut
    
    ### 🆕 Fitur Baru:
    - **Multi-select** untuk produk dan lokasi
    - **Kolom createdt** ditampilkan dalam hasil query
    - **Tren dinamis** berdasarkan jenis tanggal yang dipilih
    """)
