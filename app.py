import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import OperationalError

st.set_page_config(
    page_title="Integrated Data Management System",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Streamlit + Neon PostgreSQL Connection Test")

# --- STEP 1: Ambil konfigurasi dari Streamlit Secrets ---
try:
    db = st.secrets["connections"]["neon"]
except Exception as e:
    st.error("❌ Tidak menemukan konfigurasi database di secrets.")
    st.stop()

# --- STEP 2: Coba koneksi ke Neon PostgreSQL ---
def create_connection():
    try:
        conn = psycopg2.connect(
            host=db["host"],
            database=db["database"],
            user=db["user"],
            password=db["password"],
            port=db["port"],
            sslmode=db.get("sslmode", "require")
        )
        return conn
    except OperationalError as e:
        st.error(f"❌ Gagal konek ke database: {e}")
        return None

conn = create_connection()

# --- STEP 3: Jika konek, jalankan query test ---
if conn:
    try:
        df = pd.read_sql("SELECT NOW() AS server_time;", conn)
        st.success("✅ Koneksi ke Neon PostgreSQL berhasil!")
        st.dataframe(df)
    except Exception as e:
        st.error(f"⚠️ Gagal menjalankan query: {e}")
    finally:
        conn.close()
else:
    st.warning("⚠️ Mode demo aktif - menampilkan data contoh.")
    df_demo = pd.DataFrame({
        "member_id": ["MEM001", "MEM002"],
        "full_name": ["John Doe", "Jane Smith"],
        "country": ["Indonesia", "Malaysia"],
        "join_date": ["2024-01-01", "2024-01-02"]
    })
    st.dataframe(df_demo)
