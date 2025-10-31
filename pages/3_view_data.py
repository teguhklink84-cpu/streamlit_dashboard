import streamlit as st
import pandas as pd
import psycopg2

st.title("📋 View Data from Database")
db = st.secrets["connections"]["neon"]

conn = psycopg2.connect(**db)
cur = conn.cursor()
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema='public';
""")
tables = [t[0] for t in cur.fetchall()]
cur.close()

if tables:
    table_choice = st.selectbox("Pilih tabel:", tables)
    limit = st.slider("Jumlah baris:", 5, 200, 50)

    query = f'SELECT * FROM "{table_choice}" LIMIT {limit};'
    df = pd.read_sql(query, conn)
    st.dataframe(df)
else:
    st.warning("Belum ada tabel di database.")
conn.close()
