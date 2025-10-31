import streamlit as st
import pandas as pd
import psycopg2
from io import StringIO

st.title("📤 Import CSV Data to Neon Database")

db = st.secrets["connections"]["neon"]

uploaded_file = st.file_uploader("📁 Upload CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head())

    table_choice = st.selectbox("Pilih tabel tujuan:", ["members", "sales"])

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

        output = StringIO()
        df.to_csv(output, sep='\t', header=False, index=False)
        output.seek(0)

        try:
            cur.copy_from(output, table_choice, null="")
            conn.commit()
            st.success(f"✅ Data berhasil di-import ke tabel '{table_choice}'!")
        except Exception as e:
            st.error(f"⚠️ Error saat import: {e}")
        finally:
            cur.close()
            conn.close()
