import streamlit as st
import pandas as pd
import psycopg2
from io import StringIO

st.title("📤 Import CSV Data ke Neon Database")

db = st.secrets["connections"]["neon"]

uploaded_file = st.file_uploader("📁 Upload CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # 🧹 Bersihkan karakter newline di dalam file
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        cleaned = content.replace("\r", " ").replace("\n\n", "\n")
        uploaded_file = StringIO(cleaned)

        # 📄 Baca file CSV
        df = pd.read_csv(uploaded_file, sep=None, engine="python")

        st.success(f"✅ File terbaca dengan {len(df)} baris dan {len(df.columns)} kolom.")
        st.dataframe(df.head())

        table_name = st.text_input("🆕 Nama tabel tujuan di Neon:", "sales_data")

        if st.button("🚀 Import ke Database"):
            conn = psycopg2.connect(
                host=db["host"],
                database=db["database"],
                user=db["user"],
                password=db["password"],
                port=db["port"],
                sslmode=db.get("sslmode", "require")
            )
            cur = conn.cursor()

            # 🧱 Buat tabel otomatis jika belum ada
            columns = ", ".join([f'"{c}" TEXT' for c in df.columns])
            create_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns});'
            cur.execute(create_query)
            conn.commit()

            # 🧹 Hapus tabel lama (opsional replace)
            replace = st.checkbox("♻️ Ganti tabel lama (DROP sebelum import)?", value=False)
            if replace:
                cur.execute(f'DROP TABLE IF EXISTS "{table_name}";')
                conn.commit()
                cur.execute(f'CREATE TABLE "{table_name}" ({columns});')
                conn.commit()

            # 🚚 Import data
            output = StringIO()
            df.to_csv(output, sep='\t', header=False, index=False)
            output.seek(0)
            cur.copy_from(output, table_name, null="")
            conn.commit()

            st.success(f"✅ {len(df)} baris berhasil di-import ke tabel '{table_name}'!")
            cur.close()
            conn.close()

    except Exception as e:
        st.error(f"⚠️ Terjadi error saat import: {e}")
