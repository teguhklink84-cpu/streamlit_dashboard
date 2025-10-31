import streamlit as st
import pandas as pd
import psycopg2

st.title("🧮 SQL Query Executor")
db = st.secrets["connections"]["neon"]

query = st.text_area("Tulis query SQL:", "SELECT NOW();")

if st.button("▶️ Jalankan Query"):
    try:
        conn = psycopg2.connect(**db)
        df = pd.read_sql(query, conn)
        st.dataframe(df)
        conn.close()
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
