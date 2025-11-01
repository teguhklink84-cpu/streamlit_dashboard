import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="📊 Sales per Product per Location", layout="wide")
st.title("📦 Sales per Product per Location (LOC)")

# --- Database Connection ---
db = st.secrets["connections"]["neon"]

# Fungsi untuk ambil unique values dari kolom
@st.cache_data(ttl=3600)
def get_unique_values(column_name):
    try:
        conn = psycopg2.connect(
            host=db["host"],
            database=db["database"],
            user=db["user"],
            password=db["password"],
            port=db["port"],
            sslmode=db.get("sslmode", "require")
        )
        query = f"SELECT DISTINCT \"{column_name}\" FROM sales_data ORDER BY \"{column_name}\";"
        df = pd.read_sql(query, conn)
        conn.close()
        return df[column_name].dropna().tolist()
    except Exception as e:
        st.warning(f"Gagal mengambil data unik untuk kolom {column_name}: {e}")
        return []

# --- Sidebar Filter Section ---
st.sidebar.header("🔍 Filter Pencarian")

# Jenis tanggal untuk filter
date_type = st.sidebar.selectbox(
    "Pilih tipe tanggal:",
    ["createdt", "batchdt", "bnsperiod"]
)

# Range tanggal
col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Dari tanggal")
end_date = col2.date_input("Sampai tanggal")

# Ambil daftar produk dan lokasi
with st.spinner("🔄 Memuat daftar produk & lokasi..."):
    kode_produk_list = get_unique_values("kodeProduk")
    nama_produk_list = get_unique_values("namaProduk")
    loccd_list = get_unique_values("loccd")

# Filter produk (dropdown)
kode_produk = st.sidebar.selectbox("Kode Produk", ["All"] + kode_produk_list)
nama_produk = st.sidebar.selectbox("Nama Produk", ["All"] + nama_produk_list)

# Filter lokasi (dropdown)
loc_option = st.sidebar.selectbox("Lokasi (LOC)", ["All"] + loccd_list)

# Tombol untuk eksekusi
run_query = st.sidebar.button("🚀 Tampilkan Data")

# --- Jalankan Query Saat Klik ---
if run_query:
    if not (start_date and end_date):
        st.warning("⚠️ Harap isi rentang tanggal terlebih dahulu.")
    else:
        try:
            conn = psycopg2.connect(
                host=db["host"],
                database=db["database"],
                user=db["user"],
                password=db["password"],
                port=db["port"],
                sslmode=db.get("sslmode", "require")
            )

            # Base query
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

            # Tambah filter produk
            if kode_produk != "All":
                query += " AND \"kodeProduk\" = %s"
                params.append(kode_produk)

            if nama_produk != "All":
                query += " AND \"namaProduk\" = %s"
                params.append(nama_produk)

            # Tambah filter lokasi
            if loc_option != "All":
                query += " AND loccd = %s"
                params.append(loc_option)

            query += """
                GROUP BY bnsperiod, loccd, "namaProduk"
                ORDER BY bnsperiod DESC, loccd, total_qty DESC
            """

            # Eksekusi
            df = pd.read_sql(query, conn, params=params)

            if df.empty:
                st.warning("⚠️ Tidak ada data untuk filter tersebut.")
            else:
                st.success(f"✅ Ditemukan {len(df)} baris data.")
                st.dataframe(df, use_container_width=True)

                # Grafik per produk
                with st.expander("📊 Lihat Grafik"):
                    st.bar_chart(df, x="namaProduk", y="total_qty")

        except Exception as e:
            st.error(f"❌ Error saat menjalankan query: {e}")

        finally:
            if 'conn' in locals():
                conn.close()
else:
    st.info("🕐 Isi filter di sidebar lalu klik **'🚀 Tampilkan Data'** untuk menampilkan hasil.")
