import streamlit as st
import pandas as pd
import psycopg2
from io import StringIO

st.title("📤 Import CSV Data ke Neon Database")

# --- Ambil konfigurasi database dari secrets.toml ---
db = st.secrets["connections"]["neon"]

# --- Upload file CSV ---
uploaded_file = st.file_uploader("📁 Upload file CSV", type=["csv"])

if uploaded_file is not None:
    st.info("📄 Membaca file CSV...")

    # Coba baca file dengan encoding & separator otomatis
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8", sep=None, engine="python")
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding="latin1", sep=None, engine="python")

    st.success(f"✅ File terbaca dengan {len(df)} baris dan {len(df.columns)} kolom.")
    st.dataframe(df.head())

    # --- Pilihan tabel tujuan ---
    table_choice = st.selectbox("📦 Pilih tabel tujuan:", ["members", "sales"])

    # --- Jika user klik tombol import ---
    if st.button("🚀 Import ke Database"):
        try:
            # Koneksi ke Neon PostgreSQL
            conn = psycopg2.connect(
                host=db["host"],
                database=db["database"],
                user=db["user"],
                password=db["password"],
                port=db["port"],
                sslmode=db.get("sslmode", "require")
            )
            cur = conn.cursor()

            # Ambil nama kolom di tabel tujuan
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_choice}'
                ORDER BY ordinal_position;
            """)
            db_cols = [row[0] for row in cur.fetchall()]

            st.write(f"📋 Kolom di tabel '{table_choice}': {db_cols}")
            st.write(f"📄 Kolom di CSV: {list(df.columns)}")

            # Samakan kolom CSV dengan kolom tabel (jika nama cocok)
            df = df[[c for c in db_cols if c in df.columns]]

            # Cek apakah jumlah kolom cocok
            if len(df.columns) != len(db_cols):
                st.warning(
                    f"⚠️ Jumlah kolom tidak cocok: "
                    f"CSV ({len(df.columns)}) vs Tabel ({len(db_cols)})"
                )

            # Siapkan data ke format untuk COPY
            output = StringIO()
            df.to_csv(output, sep='\t', header=False, index=False)
            output.seek(0)

            # Jalankan COPY ke tabel
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
