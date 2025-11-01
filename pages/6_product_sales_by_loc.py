import streamlit as st
import pandas as pd
import psycopg2

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

# 🔍 Ambil master dropdown
produk_df = get_data("""
    SELECT DISTINCT "kodeProduk", "namaProduk" 
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
        start_date = st.date_input("Tanggal Mulai")
    with col2:
        end_date = st.date_input("Tanggal Akhir")
        loccd = st.selectbox("Kode Lokasi", ["ALL"] + sorted(loc_df["loccd"].tolist()))
    with col3:
        # dropdown dinamis
        kode_produk = st.selectbox("Kode Produk", ["ALL"] + sorted(produk_df["kodeProduk"].unique().tolist()))
        # kalau pilih kode_produk → namaProduk auto filter
        if kode_produk != "ALL":
            nama_produk_opsi = produk_df.loc[
                produk_df["kodeProduk"] == kode_produk, "namaProduk"
            ].unique().tolist()
        else:
            nama_produk_opsi = sorted(produk_df["namaProduk"].unique().tolist())
        nama_produk = st.selectbox("Nama Produk", ["ALL"] + nama_produk_opsi)

    submitted = st.form_submit_button("🚀 Jalankan Query")

# ⚙️ Logika sinkronisasi 2 arah
# Jika user memilih namaProduk, otomatis filter kodeProduk juga
if submitted and kode_produk == "ALL" and nama_produk != "ALL":
    try:
        kode_produk_filter = produk_df.loc[
            produk_df["namaProduk"] == nama_produk, "kodeProduk"
        ].unique().tolist()
        if len(kode_produk_filter) == 1:
            kode_produk = kode_produk_filter[0]
    except Exception:
        pass

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

        query = f"""
            SELECT 
                bnsperiod,
                loccd,
                "namaProduk",
                SUM("totalQty_contrib"::numeric) AS total_qty
            FROM sales_data
            WHERE ("{date_type}"::date) BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if kode_produk != "ALL":
            query += ' AND "kodeProduk" = %s'
            params.append(kode_produk)

        if nama_produk != "ALL":
            query += ' AND "namaProduk" = %s'
            params.append(nama_produk)

        if loccd != "ALL":
            query += ' AND loccd = %s'
            params.append(loccd)

        query += """
            GROUP BY bnsperiod, loccd, "namaProduk"
            ORDER BY bnsperiod DESC, loccd, total_qty DESC
        """

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if not df.empty:
            st.success(f"✅ {len(df)} baris ditemukan.")
            st.dataframe(df, use_container_width=True)

            # 💾 Download tombol
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="sales_by_location.csv",
                mime="text/csv",
            )
        else:
            st.warning("⚠️ Tidak ada data ditemukan untuk filter tersebut.")
    except Exception as e:
        st.error(f"❌ Error saat menjalankan query: {e}")
