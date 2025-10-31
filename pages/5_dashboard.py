import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

st.title("📈 Sales Dashboard")
db = st.secrets["connections"]["neon"]

try:
    conn = psycopg2.connect(**db)
    df = pd.read_sql('SELECT * FROM "sales_data" LIMIT 5000;', conn)
    conn.close()

    st.write("📊 Data Sampel:")
    st.dataframe(df.head())

    if "createdt" in df.columns:
        df["createdt"] = pd.to_datetime(df["createdt"], errors="coerce")
        daily = df.groupby(df["createdt"].dt.date).size().reset_index(name="transactions")
        fig = px.line(daily, x="createdt", y="transactions", title="Transaksi per Tanggal")
        st.plotly_chart(fig, use_container_width=True)

    if "namaProduk" in df.columns:
        top = df["namaProduk"].value_counts().head(10).reset_index()
        top.columns = ["namaProduk", "jumlah"]
        fig2 = px.bar(top, x="namaProduk", y="jumlah", title="Top 10 Produk Terjual")
        st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Tidak dapat memuat data: {e}")
