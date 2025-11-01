import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

st.set_page_config(page_title="📊 Sales by Location", layout="wide")
st.title("📊 Laporan Penjualan per Product & Location")

db = st.secrets["connections"]["neon"]

# Layout dua kolom: kiri (hasil), kanan (form)
col1, col2 = st.columns([3, 1])

with col2:  # Form di sebelah kanan
    st.subheader("🔍 Filter Data")

    date_type = st.selectbox("Pilih jenis tanggal:", ["createdt", "batchdt", "bnsperiod"])
    start_date = st.date_input("Tanggal mulai")
    end_date = st.date_input("Tanggal akhir")

    kode_produk = st.text_input("Kode Produk (optional)")
    nama_produk = st.text_input("Nama Produk (optional)")
    loccd = st.text_input("Kode Lokasi (optional, ketik 'ALL' untuk semua)")

    run_query = st.button("🚀 Jalankan Query")

with col1:
    if run_query:
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

            if kode_produk:
                query += ' AND "kodeProduk" ILIKE %s'
                params.append(f"%{kode_produk}%")

            if nama_produk:
                query += ' AND "namaProduk" ILIKE %s'
                params.append(f"%{nama_produk}%")

            if loccd and loccd.upper() != "ALL":
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
            else:
                st.warning("⚠️ Tidak ada data ditemukan untuk filter tersebut.")
        except Exception as e:
            st.error(f"❌ Error saat menjalankan query: {e}")
