# pages/5_dashboard.py
import streamlit as st
import pandas as pd
import psycopg2

st.title("📈 Sales Dashboard")
db = st.secrets["connections"]["neon"]

# Try import plotly, but fallback gracefully if not installed
try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

def get_sales_sample(limit=5000):
    try:
        conn = psycopg2.connect(**db)
        df = pd.read_sql('SELECT * FROM "sales_data" LIMIT %s;', conn, params=(limit,))
        conn.close()
        return df
    except Exception as e:
        st.error(f"⚠️ Tidak dapat memuat data dari DB: {e}")
        return pd.DataFrame()

df = get_sales_sample(5000)

if df.empty:
    st.warning("Belum ada data untuk ditampilkan.")
else:
    st.write("📊 Data Sampel:")
    st.dataframe(df.head())

    # Plot transaksi per tanggal (gunakan kolom 'createdt' bila ada)
    if "createdt" in df.columns:
        df["createdt_parsed"] = pd.to_datetime(df["createdt"], errors="coerce")
        daily = df.dropna(subset=["createdt_parsed"]).groupby(df["createdt_parsed"].dt.date).size().reset_index(name="transactions")
        daily = daily.sort_values("createdt_parsed")

        if not daily.empty:
            if HAS_PLOTLY:
                fig = px.line(daily, x="createdt_parsed", y="transactions", title="Transaksi per Tanggal")
                st.plotly_chart(fig, use_container_width=True)
            else:
                # fallback: Streamlit native chart
                daily_indexed = daily.set_index("createdt_parsed")
                st.line_chart(daily_indexed["transactions"])

    # Top produk terjual (kolom 'namaProduk')
    if "namaProduk" in df.columns:
        top = df["namaProduk"].value_counts().head(10).reset_index()
        top.columns = ["namaProduk", "jumlah"]

        if not top.empty:
            st.markdown("#### 🔝 Top 10 Produk Terjual")
            if HAS_PLOTLY:
                fig2 = px.bar(top, x="namaProduk", y="jumlah", title="Top 10 Produk Terjual")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.bar_chart(top.set_index("namaProduk")["jumlah"])

    # Additional quick stats
    st.markdown("### 📌 Quick Stats")
    st.metric("Total baris sampel", len(df))
    if "tdp" in df.columns:
        try:
            df["tdp_num"] = pd.to_numeric(df["tdp"], errors="coerce")
            st.metric("Total TDP (sum sample)", int(df["tdp_num"].sum()))
        except:
            pass

    # Show raw SQL sample option
    with st.expander("🔎 SQL Sample (lihat 50 baris)"):
        st.code('SELECT * FROM "sales_data" LIMIT 50;')
        st.dataframe(df.head(50))
