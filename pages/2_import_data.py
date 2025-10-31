import streamlit as st
import pandas as pd
import psycopg2
from io import StringIO

st.title("📤 Import CSV Data to Neon Database")

db = st.secrets["connections"]["neon"]

# Upload file CSV
uploaded_file = st.file_uploader("📁 Upload CSV file", type=["csv"])

if uploaded_file is not None:
    import csv

    # --- Coba baca CSV ---
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8", sep=None, engine="python")
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding="latin1", sep=None, engine="python")

    # --- Preview data ---
    st.write(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns")
    st.dataframe(df.head())

    # --- Pilih tabel tujuan ---
    table_choice = st.selectbox("📦 Pilih tabel tujuan:", ["members", "sales"])

    # --- Tombol import ---
    if st.button("🚀 Import ke Database"):
        try:
            conn = psycopg2.connect(
                host=db["host"],
                database=db["database"],
                user=db["user"],
                password=db["password"],
                port=db["port"],
                sslmode=db.get("sslmode", "require")
            )
            cur = conn.cursor()

            # Simpan ke buffer
            output = StringIO()
            df.to_csv(output, sep='\t', header=False, index=False)
            output.seek(0)

            cur.copy_from(output, table_choice, null="")
            conn.commit()

            st.success(f"✅ Data berhasil di-import ke tabel '{table_choice}'!")
        except Exception as e:
            st.error(f"⚠️ Error saat import: {e}")
        finally:
            if conn:
                cur.close()
                conn.close()
