import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="📊 Sales by Location", layout="wide")
st.title("📊 Laporan Penjualan per Produk & Lokasi")

db = st.secrets["connections"]["neon"]

# 🔍 Form Filter di atas
st.subheader("🎯 Filter Data Penjualan")

with st.form("filter_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        date_type = st.selectbox("Pilih jenis tanggal:", ["createdt", "batchdt", "bnsperiod"])
        kode_produk = st.text_input("Kode Produk (optional)")
    with col2:
        start_date = st.date_input("Tanggal Mulai")
        nama_produk = st.text_input("Nama Produk (optional)")
    with col3:
        end_date = st.date_input("Tanggal Akhir")
        loccd = st.text_input("Kode Lokasi (optional, ketik 'ALL' untuk semua)")

    submitted = st.form_submit_button("🚀 Jalankan Query")

# 📊 Eksekusi Query setelah tombol ditekan
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

            # 💾 Tambahkan tombol download
            csv = df.to_csv(index=False).encode('utf-8')
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
