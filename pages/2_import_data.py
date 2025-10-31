import streamlit as st
import pandas as pd
import psycopg2
from io import StringIO

st.title("📤 Import CSV Data ke Neon Database (Auto Table Mode)")

db = st.secrets["connections"]["neon"]

uploaded_file = st.file_uploader("📁 Upload file CSV", type=["csv"])

if uploaded_file is not None:
    st.info("📄 Membaca file CSV...")

    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8", sep=None, engine="python")
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding="latin1", sep=None, engine="python")

    st.success(f"✅ File terbaca: {len(df)} baris, {len(df.columns)} kolom.")
    st.dataframe(df.head())

    # Nama tabel (bisa pilih atau tulis baru)
    table_choice = st.text_input("📦 Masukkan nama tabel tujuan:", "sales_data")

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

            # Cek apakah tabel sudah ada
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_choice,))
            exists = cur.fetchone()[0]

            # Kalau belum ada → buat tabel baru sesuai header CSV
            if not exists:
                cols = ", ".join([f'"{c}" TEXT' for c in df.columns])
                cur.execute(f'CREATE TABLE "{table_choice}" ({cols});')
                conn.commit()
                st.info(f"🆕 Tabel baru '{table_choice}' berhasil dibuat.")

            # Convert DataFrame ke CSV (tab-separated)
            output = StringIO()
            df.to_csv(output, sep='\t', header=False, index=False)
            output.seek(0)

            # Import data ke tabel
            cur.copy_from(output, table_choice, null="", columns=df.columns)
            conn.commit()

            st.success(f"✅ {len(df)} baris berhasil di-import ke tabel '{table_choice}'!")

        except Exception as e:
            st.error(f"⚠️ Terjadi error saat import: {e}")

        finally:
            try:
                cur.close()
                conn.close()
            except:
                pass
